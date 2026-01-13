# **Debugging Deployment Gotchas: A Troubleshooting Guide**

Deployments are supposed to be smooth, but hidden issues can derail even the most routine updates. **"Deployment Gotchas"** refer to unexpected problems that occur during deployment, often due to misconfigurations, environmental mismatches, or overlooked dependencies. These issues can range from silent failures to catastrophic outages.

This guide provides a structured approach to identifying, diagnosing, and resolving common deployment gotchas efficiently.

---

## **1. Symptom Checklist**
If your deployment is failing or behaving unexpectedly, check for these common symptoms:

| **Symptom** | **Description** |
|-------------|----------------|
| **Deployments appear successful but services fail to start** | Containers/Pods show `Running` but fail to respond to requests. |
| **Environment mismatches** | Code works in staging but fails in production (e.g., missing secrets, wrong config). |
| **Resource constraints** | Pods crash due to `OutOfMemoryError` or `CPU throttling`. |
| **Service discovery issues** | Services cannot reach database, cache, or other microservices. |
| **Rollback triggers silently** | Healt checks fail, but logs don’t reveal the cause. |
| **Slow rollouts with partial failures** | Some instances deploy correctly, others fail silently. |
| **Inconsistent behavior between hosts** | Different instances of the same deployment behave differently. |
| **Logging & monitoring gaps** | No logs or metrics for critical failures. |
| **Configuration drift** | Changes persist between deployments due to misaligned configs. |

---

## **2. Common Issues & Fixes**

### **A. Silent Failures (No Logs, No Errors)**
**Scenario:** Deployment completes successfully, but the service doesn’t work.

#### **Possible Causes & Fixes**
1. **Missing Health Checks**
   - **Symptom:** App starts but health probes fail.
   - **Fix:** Ensure liveness/readiness probes are correctly configured:
     ```yaml
     # Example Kubernetes Liveness Probe
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 30
       periodSeconds: 10
     ```
   - **Debugging:**
     - Check pod logs: `kubectl logs <pod-name>`
     - Verify probe path exists: `curl http://<pod-ip>:8080/health`

2. **Environment Variable Mismatch**
   - **Symptom:** Staging works, production fails with `NullPointerException` or `Connection refused`.
   - **Fix:** Verify environment variables match between stages:
     ```sh
     # Check deployed values in Kubernetes
     kubectl get secret <secret-name> -o yaml
     ```
   - **Prevention:** Use ConfigMaps/Secrets with version control (e.g., `envsubst` in CI/CD).

3. **Database Schema Migrations Skipped**
   - **Symptom:** App crashes with `TableNotFound` errors.
   - **Fix:** Ensure migrations run before startup:
     ```java
     // Example Java app startup check
     if (!DatabaseSchema.isUpToDate()) {
         throw new RuntimeException("Schema migration failed!");
     }
     ```
   - **Debugging:** Check DB logs for migration errors.

---

### **B. Resource Constraints (OOM, CPU Throttling)**
**Scenario:** Pods crash with `Killed` or `CrashLoopBackOff`.

#### **Possible Causes & Fixes**
1. **Insufficient CPU/Memory Limits**
   - **Symptom:** Pods restart repeatedly due to `OOMKilled`.
   - **Fix:** Set proper resource limits:
     ```yaml
     resources:
       requests:
         memory: "512Mi"
         cpu: "500m"
       limits:
         memory: "1Gi"
         cpu: "1"
     ```
   - **Debugging:**
     - Check pod events: `kubectl describe pod <pod-name>`
     - Use `kubectl top pod` to monitor resource usage.

2. **Long-Running Processes Exceed Limits**
   - **Symptom:** Container consumes more memory/cpu than allocated.
   - **Fix:** Optimize code (e.g., lazy-load large objects) or adjust limits.

---

### **C. Service Discovery Failures**
**Scenario:** Microservices can’t communicate.

#### **Possible Causes & Fixes**
1. **DNS Resolution Issues**
   - **Symptom:** `Connection refused` when calling another service.
   - **Fix:** Ensure Kubernetes Service DNS works:
     ```sh
     # Test DNS resolution
     kubectl run -it --rm --restart=Never dns-test --image=busybox -- nslookup <service-name>
     ```
   - **Debugging:** Check Service endpoints:
     ```sh
     kubectl get endpoints <service-name>
     ```

2. **Port Conflicts**
   - **Symptom:** Service exposed on wrong port.
   - **Fix:** Verify port mappings in deployment:
     ```yaml
     ports:
       - name: http
         containerPort: 8080
         protocol: TCP
     ```
   - **Debugging:** Check pod IPs and ports:
     ```sh
     kubectl get pods -o wide
     kubectl exec -it <pod> -- curl localhost:8080
     ```

---

### **D. Rollback Triggers (Silent Failures)**
**Scenario:** App rolls back automatically, but no logs explain why.

#### **Possible Causes & Fixes**
1. **Health Check Failures**
   - **Symptom:** Pods restart due to liveness probe failures.
   - **Fix:** Improve health checks:
     ```python
     # Example Flask health check
     from flask import jsonify, abort

     @app.route('/health')
     def health():
         if database.is_connected():
             return jsonify({"status": "healthy"})
         else:
             abort(503)
     ```
   - **Debugging:**
     - Check probe logs: `kubectl logs <pod> --previous` (for failed probes)

2. **Configuration Errors**
   - **Symptom:** App crashes on startup with `Invalid configuration`.
   - **Fix:** Validate configs before deployment:
     ```sh
     # Example: Validate YAML before applying
     yamllint deployment.yaml
     kubectl create --validate --dry-run=client -f deployment.yaml
     ```

---

### **E. Partial Rollouts (Some Instances Fail)**
**Scenario:** Only some pods deploy correctly.

#### **Possible Causes & Fixes**
1. **Image Pull Errors**
   - **Symptom:** `ImagePullBackOff` errors.
   - **Fix:** Check image permissions and tags:
     ```yaml
     imagePullSecrets:
       - name: regcred
     ```
     - **Debugging:**
       ```sh
       kubectl describe pod <failing-pod>
       ```

2. **Init Container Failures**
   - **Symptom:** Init containers hang or fail.
   - **Fix:** Ensure init containers have proper timeouts:
     ```yaml
     initContainers:
       - name: data-sync
         image: busybox
         command: ["sh", "-c", "until ls /data; do sleep 1; done"]
         resources:
           limits:
             cpu: "100m"
     ```

---

## **3. Debugging Tools & Techniques**

| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|---------------------|
| **`kubectl logs`** | Check pod logs | `kubectl logs <pod-name> -c <container>` |
| **`kubectl describe`** | Pod/Deployment events | `kubectl describe pod <pod-name>` |
| **`kubectl exec`** | Debug inside a running container | `kubectl exec -it <pod> -- sh` |
| **`kubectl rollout`** | Check deployment status | `kubectl rollout status deployment/<name>` |
| **`traceroute`/`mtr`** | Network path analysis | `mtr <service-dns>` |
| **Prometheus/Grafana** | Metrics & performance | Check CPU/Memory usage over time |
| **`strace`/`ltrace`** | Low-level process debugging | `strace -p <PID>` (inside container) |
| **`curl`/`telnet`** | Test connectivity | `curl http://<service>:<port>` |

**Advanced Debugging:**
- **Network Policies:** Check if pods are allowed to communicate:
  ```sh
  kubectl get networkpolicies
  ```
- **Sidecar Logging:** Inject Fluentd/Fluent Bit for centralized logs.
- **Distributed Tracing:** Use Jaeger/OpenTelemetry to trace requests.

---

## **4. Prevention Strategies**

### **A. Pre-Deployment Checks**
1. **Environment Parity**
   - Use **Infrastructure as Code (IaC)** (Terraform, Pulumi) to ensure consistency.
   - **Test in a staging environment identical to production.**

2. **Static Analysis & Linting**
   - **YAML:** `yamllint`, `kubeval`
   - **Code:** SonarQube, ESLint, Pylint

3. **Canary Deployments**
   - Gradually roll out changes to a small subset of users.

4. **Blue-Green Deployments**
   - Maintain two identical environments; switch traffic abruptly.

### **B. Post-Deployment Safeguards**
1. **Automated Rollback Triggers**
   - **Example (Prometheus Alertmanager):**
     ```yaml
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "High error rate on {{ $labels.instance }}"
         runbook_url: "https://runbook.example.com/errors"
     ```

2. **Feature Flags**
   - Enable/disable features dynamically (e.g., LaunchDarkly, Unleash).

3. **Chaos Engineering**
   - **Tools:** Gremlin, Chaos Mesh
   - **Tests:** Kill pods randomly to test resilience.

### **C. Observability Best Practices**
1. **Structured Logging**
   - Use JSON logs (ELK Stack, Datadog).
   - Example:
     ```javascript
     console.log(JSON.stringify({ level: 'error', message: 'DB connection failed', error: err.stack }));
     ```

2. **Distributed Tracing**
   - Use OpenTelemetry for request tracing.

3. **Synthetic Monitoring**
   - Simulate user flows (e.g., Pingdom, New Relic Synthetics).

---

## **5. Final Checklist for Smooth Deployments**
✅ **Pre-deploy:**
- [ ] Validate YAML/config files (`kubectl apply --dry-run`)
- [ ] Check image tags match (no hardcoded `latest`)
- [ ] Verify secrets/configmaps are correct
- [ ] Test health checks locally

✅ **During deployment:**
- [ ] Monitor rollout with `kubectl rollout status`
- [ ] Check pod events for failures
- [ ] Verify service endpoints (`kubectl get endpoints`)

✅ **Post-deployment:**
- [ ] Run load tests (Locust, Gatling)
- [ ] Check logs (`kubectl logs --tail=50`)
- [ ] Verify metrics (Prometheus, Datadog)

---

### **Key Takeaways**
- **Deployment Gotchas** are often caused by **environment mismatches, resource constraints, or misconfigured probes**.
- **Always use structured logging and observability tools** to catch issues early.
- **Prevent failures with canary deployments, feature flags, and automated rollback triggers**.
- **Debug systematically:** Logs → Events → Metrics → Network.

By following this guide, you can **minimize downtime, resolve issues faster, and build more resilient deployments**. 🚀