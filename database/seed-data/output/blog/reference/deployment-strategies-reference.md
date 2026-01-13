# **[Pattern] Deployment Strategies Reference Guide**

---

## **Overview**
Deployment Strategies define systematic approaches to releasing software updates in production while minimizing downtime, risk, and impact on end-users. This pattern ensures smooth transitions between versions, enforces gradual rollouts, and provides mechanisms for rollback in case of failures.

Common use cases include:
- **Zero-downtime releases** (critical systems, e.g., e-commerce platforms).
- **Controlled rollouts** (canary, blue-green, A/B testing).
- **Risk mitigation** (gradual exposure to production traffic).
- **Rollback capabilities** (reverting to a stable version if issues arise).

This guide covers core deployment strategies, their trade-offs, and implementation considerations.

---

## **1. Core Concepts & Schema Reference**

| **Strategy**       | **Description**                                                                                                                                                                                                 | **Key Characteristics**                                                                                                                                                                                                 | **Use Case**                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Big Bang**       | Immediate deployment of the entire new version to all instances.                                                                                                                                                   | Fastest deployment; highest risk. Requires minimal orchestration.                                                                                                                                                       | Non-critical systems, internal tools, or when downtime is tolerable.                         |
| **Rolling Update** | Gradually replaces instances one by one (e.g., pod-by-pod in Kubernetes).                                                                                                                                         | Low downtime; continuous availability. Moderate risk if failures occur during replacement.                                                                                                                          | Stateful services (e.g., databases, APIs) where partial failures must be avoided.             |
| **Canary**         | Routes a small percentage (~1-5%) of traffic to the new version.                                                                                                                                                  | Low risk; quick feedback loop. Requires monitoring and gradual scaling.                                                                                                                                                  | High-traffic apps (e.g., web portals) where stability is critical.                             |
| **Blue-Green**     | Maintains two identical production environments (Blue/Green). Traffic switches instantly between them.                                                                                                             | Zero downtime; instant rollback. High resource overhead (duplicating infrastructure).                                                                                                                                | Mission-critical systems (e.g., banking, SaaS platforms).                                    |
| **A/B Testing**    | Randomly splits traffic between two versions to compare performance/metrics (e.g., conversion rates).                                                                                                             | Data-driven decisions; slower rollout. Requires sophisticated routing (e.g., feature flags).                                                                                                                         | Marketing campaigns, UX experiments, or feature validation.                                  |
| **Shadow**         | Runs the new version in parallel but doesn’t serve live traffic; metrics are compared before switching.                                                                                                        | Safe validation; no production impact. High compute costs (duplication).                                                                                                                                          | High-risk features (e.g., AI models, complex workflows).                                      |
| **Red/Black**      | Similar to Blue-Green, but uses a "red" staging environment for testing before promoting to "black" (production).                                                                                              | Strict isolation; reduces risk of unintended exposure. Poor for real-time monitoring.                                                                                                                                  | Legacy systems or heavily regulated industries (e.g., healthcare).                           |
| **Feature Flags**  | Conditionally enables/disables features via code, allowing gradual rollout without redeployment.                                                                                                                 | Flexible; enables micro-rollouts. Requires flag management infrastructure (e.g., LaunchDarkly, Unleash).                                                                                                            | SaaS products, incremental feature launches.                                                   |

---

## **2. Implementation Details**

### **Key Considerations**
1. **Traffic Management**
   - Use **service meshes** (e.g., Istio, Linkerd) or **ingress controllers** (Nginx, ALB) to route traffic dynamically.
   - Implement **feature flags** (e.g., via environment variables, config files, or dedicated services) for fine-grained control.

2. **Monitoring & Observability**
   - **Metrics**: Track error rates, latency, and success rates (e.g., Prometheus + Grafana).
   - **Logging**: Correlation IDs for requests across microservices.
   - **Alerts**: Define SLOs (e.g., "99.9% availability") and trigger alerts on deviations.

3. **Rollback Mechanisms**
   - **Automated**: Use CI/CD tools (Jenkins, GitHub Actions) to revert to the last known good version if health checks fail.
   - **Manual**: Provide a fallback endpoint (e.g., `/rollback`) or configuration-driven rollback.

4. **Data Consistency**
   - For **stateful services**, ensure transactions are atomic (e.g., use distributed locks or saga pattern).
   - For **caching**, invalidate layers when deploying new versions (e.g., Redis keys prefixed with version).

5. **Resource Planning**
   - **Blue-Green/Shadow**: Double the infrastructure temporarily.
   - **Canary**: Allocate extra capacity for the test group.

---

### **Example Architectures**

#### **Canary Deployment (Kubernetes)**
```yaml
# Deployment: Stable version (Blue)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 95
  template:
    spec:
      containers:
      - name: app
        image: app:v1.0.0

# Deployment: New version (Green)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: app
        image: app:v2.0.0

# Ingress Rule (Nginx)
server {
  location / {
    proxy_pass http://app-stable;  # 95% traffic
    # Canary: Route 5% traffic via annotations or Istio
  }
}
```

#### **Blue-Green (AWS ECS)**
1. **Deploy Green**: Create a new task definition (`app:v2.0.0`) and register it.
2. **Test**: Run a load test on the green environment.
3. **Switch Traffic**:
   ```bash
   aws elbv2 modify-load-balancer-attributes --load-balancer-arn <LB_ARN> --attributes Key="routing.http2.enabled",Value="false"
   aws ecs update-service --cluster <cluster> --service <service> --force-new-deployment
   ```

---

## **3. Query Examples**

### **Checking Deployment Status (Terraform)**
```hcl
data "aws_ecs_deployment" "canary" {
  cluster_name = aws_ecs_cluster.my-cluster.name
  service_name = "my-service"
  depends_on  = [aws_ecs_service.my-service]
}

output "canary_status" {
  value = data.aws_ecs_deployment.canary.status
}
```

### **Feature Flag Validation (LaunchDarkly)**
```bash
curl -X POST \
  https://app.launchdarkly.com/api/v2/flags \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "new-dashboard",
    "variations": [
      { "value": true, "track": true, "weight": 10 },
      { "value": false, "track": true, "weight": 90 }
    ]
  }'
```

### **Rolling Update Logs (Kubernetes)**
```bash
kubectl logs -l app=app,version=v2.0.0 --tail=50
kubectl describe pod <pod-name> | grep -i "rollout"
```

---

## **4. Trade-offs & Decision Matrix**

| **Strategy**  | **Pros**                                  | **Cons**                                  | **Best For**                          |
|---------------|-------------------------------------------|-------------------------------------------|---------------------------------------|
| **Big Bang**  | Simple, fast deployments.                 | High risk; downtime.                     | Non-critical systems.                |
| **Rolling**   | Low downtime; no full reboots.           | Risk if one pod fails.                    | Stateless apps, APIs.                |
| **Canary**    | Low risk; quick feedback.                | Requires monitoring.                     | High-traffic web apps.               |
| **Blue-Green**| Zero downtime; instant rollback.        | High resource usage.                     | Mission-critical systems.            |
| **Shadow**    | Safe validation.                         | High cost; no production data.           | Experimental features.                |
| **A/B Testing**| Data-driven decisions.                   | Slow rollout; complex routing.           | Marketing campaigns.                 |
| **Feature Flags** | Flexible; no redeployment.          | Flag management overhead.                | SaaS products.                        |

---

## **5. Related Patterns**
1. **Feature Toggles (Flag Management)**
   - Complements deployment strategies by enabling/disabling features dynamically. Tools: [LaunchDarkly](https://launchdarkly.com/), [Unleash](https://unleash.io/).

2. **Circuit Breaker**
   - Prevents cascading failures during rollouts (e.g., Hystrix, Resilience4j).

3. **Saga Pattern**
   - Manages distributed transactions in stateful rollouts (e.g., database migrations).

4. **Infrastructure as Code (IaC)**
   - Ensures reproducible environments (e.g., Terraform, Pulumi) for consistent deployments.

5. **Chaos Engineering**
   - Proactively tests resilience during rollouts (e.g., Chaos Monkey, Gremlin).

6. **Progressive Delivery**
   - Combines canary, feature flags, and monitoring for automated, risk-aware rollouts (e.g., [Flagsmith](https://flagsmith.com/), [Optimizely](https://www.optimizely.com/)).

7. **Blue-Green with GitOps**
   - Uses Git workflows (e.g., ArgoCD) to automate blue-green switches.

---

## **6. Anti-Patterns & Pitfalls**
- **Skipping Testing**: Deploying without canary/shadow validation increases blast radius.
- **Ignoring Rollback Plans**: Without a rollback strategy, failures become crises.
- **Overcomplicating Traffic Routing**: Using multiple strategies (e.g., canary + blue-green) can lead to chaos.
- **Neglecting Monitoring**: Lack of observability makes it impossible to detect failures early.
- **Hardcoding Versions**: Avoid `image: app:latest`; use immutable tags (e.g., `app:v2.0.0`).

---
## **7. Tools & Frameworks**
| **Category**          | **Tools**                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| **Orchestration**     | Kubernetes, Docker Swarm, Nomad, ECS                                      |
| **Service Mesh**      | Istio, Linkerd, Consul Connect                                            |
| **CI/CD**             | Jenkins, GitHub Actions, GitLab CI, ArgoCD                                |
| **Feature Flags**     | LaunchDarkly, Unleash, Flagsmith, Optimizely                             |
| **Monitoring**        | Prometheus + Grafana, Datadog, New Relic, ELK Stack                      |
| **Database**          | Flyway, Liquibase (migrations), Vitess (scaling reads)                     |
| **Chaos Testing**     | Gremlin, Chaos Mesh, Chaos Monkey                                         |

---
## **8. Example Workflow: Canary Deployment with Kubernetes**
1. **Build & Push**:
   ```bash
   docker build -t my-app:v2.0.0 .
   docker push my-registry/my-app:v2.0.0
   ```
2. **Deploy Canary**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app-canary
   spec:
     replicas: 5
     selector:
       matchLabels:
         app: my-app
         track: canary
     template:
       spec:
         containers:
         - name: my-app
           image: my-registry/my-app:v2.0.0
   ```
3. **Route Traffic** (via Istio or Ingress):
   ```yaml
   apiVersion: networking.istio.io/v1alpha3
   kind: VirtualService
   metadata:
     name: my-app
   spec:
     hosts:
     - my-app
     http:
     - route:
       - destination:
           host: my-app.stable.svc.cluster.local
           subset: v1
         weight: 95
       - destination:
           host: my-app.canary.svc.cluster.local
           subset: v2
         weight: 5
   ```
4. **Monitor**:
   - Check metrics (e.g., `kubectl top pods`).
   - Use Prometheus alerts for errors in the canary.
5. **Promote or Rollback**:
   - If stable: Scale canary up, stable down.
   - If unstable: Roll back to stable version.

---
## **9. Further Reading**
- [Google’s SRE Book (Deployment Strategies)](https://sre.google/sre-book/deployments/)
- [Istio Canary Documentation](https://istio.io/latest/docs/tasks/traffic-management/canary/)
- [Feature Flags 101 (Martin Fowler)](https://martinfowler.com/articles/feature-toggles.html)
- [Kubernetes Rolling Updates](https://kubernetes.io/docs/tutorials/kubernetes-basics/deploy-app/deploy-image/#updating-the-application)

---
## **10. Glossary**
| **Term**          | **Definition**                                                                 |
|--------------------|---------------------------------------------------------------------------------|
| **Rollout**        | The process of deploying a new version to production.                          |
| **Traffic Splitting** | Dividing incoming requests between versions (e.g., 95% old, 5% new).         |
| **SLO**            | Service Level Objective (e.g., "99.9% availability").                           |
| **Immutable Tag**  | A fixed version tag (e.g., `v1.2.0`) vs. `latest`.                            |
| **Sidecar Proxy**  | A container (e.g., Envoy in Istio) that handles traffic routing alongside the app. |
| **Feature Flag**   | A toggle to enable/disable features in code without redeployment.              |
| **Blast Radius**   | The impact of a failure (e.g., 100% rollout = high blast radius).              |