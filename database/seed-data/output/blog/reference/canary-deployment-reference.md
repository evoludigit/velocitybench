# **[Pattern] Canary Deployments Reference Guide**

---

## **Overview**
Canary Deployments is a **risk-mitigation strategy** where updates to production systems are gradually rolled out to a **small subset of users** (typically ~1-10%) before being fully deployed to the entire user base. This minimizes exposure to failures and allows teams to **monitor performance, stability, and user impact** in real-world conditions before a full launch.

The pattern is widely used in **microservices, cloud-native applications, and continuous deployment pipelines** to balance innovation speed with operational safety. Key benefits include:
- **Reduced blast radius** (confined failures affect fewer users).
- **Immediate feedback** via metrics, logs, and user feedback.
- **Easy rollback** if issues arise (only revert the canary group).
- **A/B testing capabilities** (compare new vs. old versions).

---
## **Key Concepts & Implementation Details**
### **Core Components**
| **Component**          | **Description**                                                                                     | **Example**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Traffic Splitting**  | Routes a percentage of real user traffic to the canary version.                                      | 5% of requests → new API v2.          |
| **Feature Flags**      | Enables/disables canary behavior dynamically without redeploying.                                     | `@EnableFeatureManagement` annotation. |
| **Monitoring & Alerts** | Real-time tracking of metrics (latency, error rates, custom events).                                 | Prometheus + Grafana dashboards.     |
| **Automated Rollback** | Triggers a rollback if SLOs (Service Level Objectives) are violated.                                | Error rate > 5% for 5 mins → revert. |
| **User Segmentation**  | Targets specific user groups (e.g., by device, region, or behavior).                                 | "Mobile users in US" → canary.       |
| **Deployment Pipeline**| Integrates with CI/CD tools (Jenkins, GitHub Actions, ArgoCD) to coordinate releases.               | Argo Rollouts for GitOps.            |

---

### **Implementation Steps**
#### **1. Define Canary Criteria**
- **Scope**: Which service/component (e.g., microservice, database schema)?
- **Traffic Split**: Start with **1-5%** of users/requests.
- **Duration**: Minimum **1-2 business cycles** (e.g., 24–48 hours) for validation.
- **Rollback Plan**: Predefined conditions (e.g., error rate > threshold).

#### **2. Configure Traffic Routing**
- **Load Balancers**:
  Use weighted routing (e.g., Nginx, ALB, Istio).
  Example:
  ```yaml
  # Istio VirtualService (traffic-split.yaml)
  http:
    - route:
        - destination:
            host: new-service.default.svc.cluster.local
            subset: v2  # Canary version
          weight: 5
        - destination:
            host: old-service.default.svc.cluster.local
            subset: v1  # Stable version
          weight: 95
  ```
- **API Gateways**:
  Implement canary logic in the gateway (e.g., Kong, Traefik).
  Example (Kong):
  ```json
  {
    "plugins": [
      {
        "name": "canary",
        "config": {
          "split_type": "header",
          "header": "X-Canary",
          "value": "true",
          "canary_upstream": "new-service:8080",
          "fallback_upstream": "old-service:8080",
          "percentage": 5
        }
      }
    ]
  }
  ```

#### **3. Enable Feature Flags**
- **Server-Side**:
  Use tools like LaunchDarkly, Flagsmith, or local feature toggles.
  Example (Spring Cloud Gateway):
  ```java
  @Bean
  public RouteLocator customRouteLocator(ServerWebExchange exchange) {
      return routes ->
          routes.route("canary_route",
              r -> r.path("/api/**")
                   .filters(f -> f.filter((exchange1, chain) ->
                      if (isCanaryUser(exchange1)) {
                          exchange1.getAttributes().put("canary", true);
                      }
                      return chain.filter(exchange1);
                   ))
                   .uri("lb://new-service"));
  }
  ```
- **Client-Side**:
  Hide/unhide UI features based on a flag (e.g., React/Redux).

#### **4. Instrument Monitoring**
- **Metrics to Track**:
  | Metric               | Purpose                                                                 | Tool Example               |
  |----------------------|-------------------------------------------------------------------------|----------------------------|
  | Error Rate           | Detect failure modes in canary.                                          | Prometheus (`errors_total`).|
  | Latency (P99)        | Identify performance regressions.                                        | Datadog, New Relic.         |
  | Custom Events        | Track business-specific KPIs (e.g., "checkout_success").                 | OpenTelemetry.             |
  | User Feedback        | Crowdsource issues via surveys or error reports.                         | Sentry, UserTesting.com.   |
  - **Alerting**: Set up alerts for canary-specific thresholds (e.g., `latency_p99 > 1s`).
    Example (Prometheus Alert):
    ```yaml
    - alert: CanaryHighLatency
      expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[1m])) > 1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Canary v2 latency > 1s for 5 minutes"
    ```

#### **5. Gradual Rollout**
- **Phases**:
  1. **Canary**: 1–5% of users.
  2. **Staging**: 20–30% after validation.
  3. **Full Release**: If SLOs are met for ≥2 cycles.
- **Auto-Scaling**: Adjust canary size based on load (e.g., Kubernetes Horizontal Pod Autoscaler).

#### **6. Automated Rollback**
- **Conditions**: Trigger rollback if:
  - Error rate > 5% for 5 mins.
  - Latency P99 > threshold (e.g., 2x baseline).
  - Critical business metric drops (e.g., "active_users" by 10%).
- **Tools**:
  - **Argo Rollouts**: Built-in canary analysis and rollback.
    ```yaml
    # argo-rollouts-analysis.yaml
    apiVersion: argoproj.io/v1alpha1
    kind: AnalysisRun
    metadata:
      generateName: new-service-canary-analysis-
    spec:
      metrics:
      - name: error-rate
        threshold: ReferenceValue(0.05)  # 5% error rate max
        interval: 1m
      template:
        successCondition: success
        failureCondition: failure
    ```
  - **Custom Scripts**: Use CI/CD hooks (e.g., GitHub Actions) to trigger rollbacks.

#### **7. User Segmentation**
- **Methods**:
  - **Random Sampling**: Use canary tokens or cookies (e.g., `canary=true`).
  - **Targeted Groups**: Segment by:
    - **Device/OS** (e.g., "iOS 15+").
    - **Region** (e.g., "US West Coast").
    - **Behavior** (e.g., "power users").
  - **Tools**:
    - **Feature Management Platforms**: LaunchDarkly, Unleash.
    - **Database Queries**: Filter users via application logic.
      Example (PostgreSQL):
      ```sql
      SELECT * FROM users
      WHERE canary = true LIMIT 5000;  -- 1% of users
      ```

---
## **Schema Reference**
Below are key schemas for canary deployments, standardized for automation.

| **Schema**               | **Description**                                                                 | **Example Payload**                          |
|--------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Traffic Split**        | Defines canary % for a service/route.                                          | `{"service": "order-service", "version": "v2", "weight": 0.05}` |
| **Feature Flag**         | Enables/disables canary features for users/groups.                              | `{"key": "new_ui", "variation": "canary", "on": true, "segments": ["mobile_users"]}` |
| **Rollout Policy**       | Defines rollback conditions and phases.                                         | `{`duration`: 12h,`thresholds`: {`error_rate`: 0.05},`phases`: [1, 20, 100]}` |
| **User Segment**         | Defines groups eligible for canary exposure.                                    | `{"name": "beta_testers", "criteria": {"os": "iOS", "region": "US"}}` |

---
## **Query Examples**
### **1. Check Canary Traffic in Istio**
```bash
kubectl get -n istio-system svc istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# Redirect traffic to canary:
istioctl analyze traffic -f traffic-split.yaml
```

### **2. Feature Flag Query (LaunchDarkly)**
```bash
curl -X POST \
  https://app.launchdarkly.com/api/v2/client-side/flags/evaluate \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"key": "user123", "flags": ["new_ui"]}'
```
**Response**:
```json
{
  "new_ui": {
    "variation": 1,  // canary variation
    "on": true
  }
}
```

### **3. PromQL for Canary Metrics**
```promql
# Error rate in canary (v2)
sum(rate(http_requests_total{version="v2"}[1m]))
  / sum(rate(http_requests_total[1m]))
  by (version)

# Latency P99 comparison
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m]))
  by (le, version))
```

### **4. Kubernetes Canary Scaling**
```bash
# Scale down non-canary pods
kubectl scale deployment v1 --replicas=0
kubectl scale deployment v2 --replicas=20
```

---
## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 | **Tools/Libraries**                          |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Blue-Green Deployment** | Instant cutover between two identical environments.                         | Zero-downtime deploys with no gradual rollout.                                  | Docker Swarm, Kubernetes Argo Rollouts.       |
| **Feature Toggles**       | Dynamically enable/disable features without redeploying.                     | A/B testing, gradual feature rollouts.                                           | LaunchDarkly, Flagsmith.                     |
| **Progressive Delivery**  | Combines canary + staged rollouts with automated analysis.                  | Advanced CD strategies with self-healing.                                      | Argo Rollouts, Flagger.                      |
| **Shadow Deployments**    | Run new versions in parallel without serving traffic.                        | Smoking tests for new services.                                                 | AWS Shadow, Envoy Proxy.                     |
| **Safety Net Deployments**| Automatically revert changes if SLOs are violated (post-canary).            | High-risk releases where manual rollback is slow.                                | SLO-based alerting (e.g., Google SRE).       |

---
## **Best Practices**
1. **Start Small**: Begin with **1–5%** of traffic to detect edge cases.
2. **Monitor First**: Use **SLOs** (e.g., error budget) to define success.
3. **Automate Rollbacks**: Define **clear thresholds** (e.g., error rate > 5%).
4. **Isolate Testing**: Run canaries in **staging-like environments** before production.
5. **Communicate**: Notify users (e.g., "This release is in beta") and document the rollout.
6. **Document Rollback Steps**: Include pre-written runbooks for emergencies.
7. **Tooling**: Use **GitOps** (ArgoCD) or **SRE practices** for consistency.

---
## **Anti-Patterns**
- **No Monitoring**: Deploying canaries without observability is useless.
- **Over-Segmentation**: Targeting too many small groups slows feedback loops.
- **Manual Rollbacks**: Avoid ad-hoc decisions; automate based on metrics.
- **Ignoring User Feedback**: Canaries are useless without real user testing.
- **Skipping Staging**: Always validate canaries in a **production-like environment**.

---
## **Tools & Technologies**
| **Category**          | **Tools**                                                                                   |
|-----------------------|--------------------------------------------------------------------------------------------|
| **Service Mesh**      | Istio, Linkerd, Consul Connect.                                                          |
| **CI/CD**             | Argo Rollouts, Flagger, GitHub Actions, Jenkins.                                          |
| **Feature Flags**     | LaunchDarkly, Flagsmith, Unleash, Google Flags.                                           |
| **Observability**     | Prometheus, Grafana, Datadog, OpenTelemetry, Sentry.                                       |
| **Load Balancing**    | Nginx, AWS ALB, Envoy, Kong.                                                              |
| **GitOps**            | ArgoCD, Flux, Spinnaker.                                                                 |
| **Database**          | PostgreSQL (canary tokens), MongoDB (read preferences), CockroachDB (multi-region).      |

---
## **Example Workflow**
1. **Commit Code**: Push to `main` branch.
2. **CI Pipeline**:
   - Builds Docker image for `new-service:v2`.
   - Deploys to staging environment.
3. **Canary Deployment**:
   - Istio routes 5% of traffic to `v2`.
   - Prometheus alerts if `error_rate` > 0.05 for 5 mins.
4. **Validation**:
   - Manual review of metrics + user feedback.
   - If stable, scale canary to 20%.
5. **Full Rollout**:
   - After 2 cycles (48h) with no issues, shift all traffic to `v2`.
6. **Rollback**:
   - If P99 latency > 2x baseline, Argo Rollouts auto-reverts to `v1`.

---
## **Further Reading**
- [Argo Rollouts Canary Guide](https://argo-rollouts.readthedocs.io/)
- [Google SRE Book: Canary Analysis](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)
- [LaunchDarkly Feature Flags](https://launchdarkly.com/docs/)