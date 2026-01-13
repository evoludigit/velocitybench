# Debugging **Deployment Approaches**: A Troubleshooting Guide

---

## **Overview**
This guide covers troubleshooting common pitfalls in **Deployment Approaches**, including blue-green, canary, rolling, and feature flag deployments. The goal is to quickly identify and resolve deployment-related issues to minimize downtime and ensure smooth service delivery.

---

## **Symptom Checklist**
Before diving into fixes, verify if your deployment-related issue aligns with the following symptoms:

| **Symptom**                                  | **Likely Cause**                          | **Severity** |
|---------------------------------------------|------------------------------------------|--------------|
| Incomplete rollout (e.g., traffic not routed correctly) | Misconfigured routing rules (e.g., ALB, NLB, or service mesh) | High |
| High error rates (5xx responses) during deployment | New version crashes due to misconfigurations, missing dependencies, or environment drift | Critical |
| Users experience inconsistent behavior (e.g., partial rollback) | Canary/regression traffic not handled correctly | Medium |
| Deployment stuck (e.g., pending or failed) | Issues with CI/CD pipeline, permission errors, or resource constraints | Medium |
| Slow rollout (traffic not shifting quickly) | Slow health checks, misconfigured rollout thresholds | Low-Medium |
| Feature flags not behaving as expected | Incorrect flag evaluations or inconsistent environments | Medium |
| Database inconsistencies post-deployment | Incomplete schema migrations or connection issues | Critical |

---

## **Common Issues and Fixes**

### **1. Blue-Green Deployment Failures**
**Symptom:** Traffic is misrouted, causing downtime or inconsistent user experiences.
**Root Causes:**
- Incorrect load balancer configuration (e.g., wrong target group, health check misconfigurations).
- Environment drift (e.g., stale configs in green environment).
- Database outages (e.g., write conflicts during cutover).

#### **Debugging Steps & Fixes**
**A. Verify Load Balancer Setup**
- Check CloudWatch (AWS) or equivalent metrics for `TargetHealthDesired` vs. `TargetHealthUnhealthy`.
- **Fix:** Update ALB/NLB targets to point to the correct green environment.
  ```bash
  # Example: Update ALB target group for AWS
  aws elbv2 modify-target-group-attributes \
    --target-group-arn <TARGET_GROUP_ARN> \
    --attributes Key=target_type,Value=instance
  ```
- Ensure health checks match your app’s endpoint (e.g., `/health`).
  ```json
  # Example health check config for AWS ALB
  {
    "HealthyThresholdCount": 2,
    "Interval": 30,
    "Path": "/health",
    "Port": "traffic-port",
    "TargetValue": "200-299,301-307",
    "Timeout": 5,
    "UnhealthyThresholdCount": 5
  }
  ```

**B. Check for Environment Drift**
- Use tools like **Terraform drift detection** or **Ansible` inventory diffs** to compare environments.
  ```bash
  # Example: Check Terraform drift
  terraform plan -out=tfplan && terraform show -json tfplan | jq '.planned_values.root_module.resources[] | select(.changes[].action=="no-op")'
  ```
- **Fix:** Reapply configs or restore from a known-good state.

**C. Database Cutover Issues**
- Ensure writes to the old DB are blocked during cutover (use database triggers or application-level locks).
  ```sql
  -- Example: Disable writes during blue-green switch (PostgreSQL)
  ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
  ```
- **Fix:** Use a **double-write pattern** during transition to avoid data loss.

---

### **2. Canary Deployment Traffic Misrouting**
**Symptom:** Only a subset of users hit the new version, but errors persist, and traffic isn’t scaled correctly.
**Root Causes:**
- Incorrect canary percentage in service mesh (Istio) or proxy (Nginx, HAProxy).
- Health checks failing for the new version.
- Missing circuit breakers (e.g., Retry or Timeout policies).

#### **Debugging Steps & Fixes**
**A. Validate Traffic Splitting**
- Check Istio’s metrics or proxy logs:
  ```bash
  # Example: Istio canary traffic analysis
  kubectl get servicemeshmemberaccessreview -n istio-system
  kubectl get destinationrule -n <namespace> -o yaml | grep -A 10 "trafficSplit"
  ```
- **Fix:** Adjust traffic splitting rules:
  ```yaml
  # Example: Istio DestinationRule for canary
  apiVersion: networking.istio.io/v1alpha3
  kind: DestinationRule
  metadata:
    name: myapp-dr
  spec:
    host: myapp
    trafficPolicy:
      loadBalancer:
        simple: LEAST_CONN
      outlierDetection:
        consecutiveErrors: 5
        interval: 10s
  ```
- Ensure health checks are passing:
  ```bash
  # Example: Test health check endpoint
  curl -I http://<canary-pod-ip>:<port>/health
  ```

**B. Circuit Breaker Misconfigurations**
- If using **Envoy/Haproxy**, check for timeouts or retries:
  ```bash
  # Example: Check Envoy stats
  curl http://localhost:15000/stats/pairs?match[]=envoy.http.canonical_service_config
  ```
- **Fix:** Adjust retry policies or increase timeouts:
  ```yaml
  # Example: Envoy retry policy
  retries:
    attempts: 3
    retry_on: gateway-error,connect-failure,refused-stream
    perTryTimeout: 2s
  ```

---

### **3. Rolling Deployment Stalls**
**Symptom:** Deployments hang at a certain percentage (e.g., stuck at 90%).
**Root Causes:**
- Slow health checks (e.g., long DB queries).
- Pod evictions due to resource constraints.
- Liveness probe misconfigurations.

#### **Debugging Steps & Fixes**
**A. Check Pod Events**
- Inspect Kubernetes events:
  ```bash
  kubectl describe deploy/myapp -n <namespace>
  ```
- Look for `Warning` events like `FailedScheduling`, `CrashLoopBackOff`, or `Pending`.

**B. Adjust Liveness/Readiness Probes**
- If probes are too strict, reduce timeouts or failure thresholds:
  ```yaml
  # Example: Kubernetes liveness probe adjustments
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30  # Increased from default 0
    periodSeconds: 10         # Reduced from default 10
    failureThreshold: 3       # Reduced from default 3
  ```

**C. Scale Up Resources**
- Check resource requests/limits:
  ```bash
  kubectl top pods -n <namespace>
  ```
- **Fix:** Increase CPU/memory requests or add a horizontal pod autoscaler (HPA):
  ```yaml
  # Example: HPA spec
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: myapp-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: myapp
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

### **4. Feature Flag Rollback Issues**
**Symptom:** Feature flags behave differently across environments (e.g., dev works, prod doesn’t).
**Root Causes:**
- Flag evaluation logic is environment-dependent (e.g., hardcoded values).
- Cache stale flags (e.g., Redis not syncing across environments).
- Incorrect user segmentation (e.g., wrong A/B test groups).

#### **Debugging Steps & Fixes**
**A. Validate Flag Evaluations**
- Check flag service logs (e.g., LaunchDarkly, Flagsmith):
  ```bash
  # Example: Query feature flag evaluations (Flagsmith)
  curl -X GET "http://flagsmith-api:8000/api/v1/flags/evaluate/" \
       -H "Authorization: Bearer <TOKEN>" \
       -d '{"key": "new_feature", "environment": "production"}'
  ```
- **Fix:** Ensure flags are evaluated consistently:
  ```python
  # Example: Python flag checking (using Flagsmith)
  from flagsmith import Client
  client = Client("https://your-flagsmith-url", "<API_KEY>")
  flag = client.get_flag("new_feature", environment="production")
  if flag.is_enabled():
      # Enable feature
  ```

**B. Sync Cache Across Environments**
- If using Redis, ensure it’s shared or use a distributed cache:
  ```bash
  # Example: Redis cluster setup (for multi-env)
  redis-cli --cluster create \
    $(for i in {1..6}; do echo node-1-$(printf "%02d" $i).example.com:6379; done) \
    --cluster-replicas 1
  ```

**C. Debug User Segmentation**
- Verify rollout percentages match expectations:
  ```bash
  # Example: Check LaunchDarkly rollout
  curl -X GET "https://app.launchdarkly.com/api/v2/flags/new_feature/rollouts" \
       -H "Authorization: Bearer <TOKEN>"
  ```
- **Fix:** Adjust segment definitions or use feature management tools with precise targeting.

---

## **Debugging Tools and Techniques**
| **Tool/Technique**               | **Purpose**                                                                 | **Example Command/Use Case**                          |
|-----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **Kubernetes `kubectl describe`** | Debug pod/deployment issues (e.g., crashes, resource limits).               | `kubectl describe pod myapp-7c8f5b9d5-abc12`          |
| **Prometheus + Grafana**          | Monitor deployment health (e.g., error rates, latency).                     | Query: `rate(http_requests_total{status=~"5.."}[1m])` |
| **Envoy/Istio Metrics**           | Inspect traffic routing, errors, and circuit breakers.                       | `curl http://localhost:9901/metrics | grep envoy_http`   |
| **Terraform Plan**                | Detect infrastructure drift.                                                | `terraform plan -out=tfplan`                         |
| **Chaos Engineering (Gremlin)**   | Test failure recovery during deployments.                                   | Simulate pod kills: `kubectl delete pod myapp-1`     |
| **Feature Flag Dashboards**       | Track A/B test results and flag toggles.                                     | LaunchDarkly/BrowserStack UI                        |
| **Distributed Tracing (Jaeger)**  | Debug latency spikes in new deployments.                                     | `jaeger query --service=myapp --duration=5m`        |
| **CI/CD Pipeline Logs**           | Check build/deploy failures (e.g., failed unit tests).                     | `gitlab-ci debug` or `jenkins build log`             |

---

## **Prevention Strategies**
### **1. Automated Rollback Mechanisms**
- **Health-Based Rollback:** Automatically revert if error rates exceed thresholds.
  ```yaml
  # Example: Kubernetes rollback on error
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: myapp
  spec:
    revisionHistoryLimit: 3
    rollbackOnConfigChange: true
  ```
- **Feature Flag Rollback:** Use tools like LaunchDarkly to auto-revert flags if metrics degrade.

### **2. Canary Analysis with Automated Approval**
- Use **SLO-based approvals** (e.g., error rate < 1%, latency < 500ms).
- Example workflow:
  ```mermaid
  graph TD
    A[Deploy Canary] --> B{Check Error Rate < 1%?}
    B -->|Yes| C[Promote to Prod]
    B -->|No| D[Rollback & Alert]
  ```

### **3. Infrastructure as Code (IaC) for Reproducible Deployments**
- **Terraform/CloudFormation:** Ensure environments are identical.
  ```hcl
  # Example: Terraform module for blue-green
  module "blue-green" {
    source = "./modules/blue-green"
    stage   = "production"
    env_vars = {
      DB_HOST = "prod-db"
    }
  }
  ```
- **GitOps (ArgoCD/Flux):** Sync Kubernetes manifests from Git to avoid config drift.

### **4. Observable Deployments**
- **Metrics First:** Instrument all deployments with Prometheus/Grafana.
  ```bash
  # Example: Prometheus alert for high error rates
  ALERT HighErrorRate
    IF rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    FOR 1m
    LABELS {severity="critical"}
  ```
- **Distributed Tracing:** Use Jaeger to track latency bottlenecks.

### **5. Pre-Deployment Validation**
- **Unit/Integration Tests:** Run tests before canary deployment.
  ```bash
  # Example: Run tests in CI before canary
  make test-e2e
  ```
- **Load Testing:** Simulate production traffic with tools like Locust or k6.
  ```bash
  # Example: Locust load test
  locust -f locustfile.py --headless -u 1000 -r 100 --host=http://myapp:8080
  ```

### **6. Documentation and Runbooks**
- **Deployment Playbooks:** Document steps for rollback, canary analysis, and critical fixes.
  ```markdown
  # Blue-Green Rollback Runbook
  1. Verify traffic is misrouted (check ALB metrics).
  2. Switch load balancer to old version.
  3. Monitor for 15 mins; if stable, proceed to step 4.
  4. Delete new environment pods.
  ```
- **Postmortems:** After incidents, update runbooks with lessons learned.

---

## **Conclusion**
Deployment failures are inevitable, but systematic debugging and prevention strategies can minimize downtime. Focus on:
1. **Quick validation** (check logs, metrics, and routing).
2. **Automated rollback** for quick recovery.
3. **Observability** to detect issues before they affect users.
4. **Prevention** via IaC, testing, and runbooks.

For complex issues, leverage tools like **Chaos Engineering** to proactively test failure modes. Always prioritize **minimal viable deployment**—start small (e.g., 5% canary) and expand only if metrics are green.

---
**Next Steps:**
- Audit your current deployment strategy for gaps.
- Implement automated rollback and observability.
- Document runbooks for critical paths.