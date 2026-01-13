# **[Pattern] Deployment Techniques – Reference Guide**

---

## **Overview**
The **Deployment Techniques** pattern encompasses strategies, methodologies, and best practices for delivering software applications, services, and infrastructure changes to production or operational environments. Effective deployment ensures minimal downtime, predictable rollouts, and quick recovery from failures. This pattern categorizes deployment techniques into **classic** (e.g., *Blue-Green*, *Canary*) and **modern** (e.g., *Progressive Delivery*, *Feature Flags*), along with their use cases, trade-offs, and automation considerations. It also covers pre-deployment checks, rollback mechanisms, and integration with CI/CD pipelines.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **When to Use**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Deployment**         | The process of releasing software/infrastructure changes to an environment.                       | When moving code, configurations, or dependencies to a live or staging environment.               |
| **Rollout**            | Gradually deploying changes to a subset of users/traffic.                                          | Testing stability in production with minimal risk (e.g., Canary, Blue-Green).                      |
| **Rollback**           | Reverting to a previous stable state due to failures.                                             | When deployments introduce critical bugs or performance degradation.                             |
| **Zero-Downtime**      | Ensuring no service interruption during deployment.                                                | Critical systems requiring 99.99% uptime (e.g., e-commerce platforms).                            |
| **Feature Flags**      | Toggling feature visibility dynamically without redeploying code.                                  | Gradually exposing new features to users or A/B testing.                                          |

---

## **Deployment Techniques Schema Reference**

| **Technique**          | **Description**                                                                                   | **Pros**                                                                                          | **Cons**                                                                                          | **Best For**                                                                                       |
|------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Blue-Green**         | Deploying to a *staging* ("Green") environment while the *live* ("Blue") remains active.         | Zero downtime, instant rollback.                                                                 | High resource usage (duplicate environments).                                                  | Critical services with strict SLA requirements.                                                   |
| **Canary**             | Gradually shifting traffic to a new deployment (e.g., 5% → 100%).                                  | Early bug detection, reduced risk.                                                               | Requires monitoring and traffic management.                                                    | High-traffic apps where gradual rollout is acceptable.                                            |
| **Rolling Update**     | Replacing instances one-by-one while maintaining availability.                                      | Minimal downtime, gradual testing.                                                              | Risk of partial failures during transition.                                                     | Stateless applications (e.g., microservices).                                                   |
| **Progressive Delivery** | Combines Canary + feature flags for fine-grained control.                                        | Flexible rollout with dynamic toggles.                                                            | Complex setup (requires feature management platform).                                          | Dynamic features needing A/B testing or staged releases.                                          |
| **Feature Flags**      | Enabling/disabling features via configuration without redeploying code.                           | Quick iteration, reduced risk.                                                                   | Flag management overhead (e.g., tracking, permissions).                                        | Startups or teams with rapid feature cycles.                                                    |
| **Dark Launch**        | Deploying unseen to hidden users until validated.                                                 | Undisturbed UX, pre-launch testing.                                                              | No immediate feedback from end users.                                                           | New features needing secret testing before release.                                               |
| **A/B Testing**        | Comparing two versions (A vs. B) with different user segments.                                      | Data-driven decisions.                                                                           | Requires statistical analysis and user segmentation.                                           | Marketing campaigns or UI/UX experiments.                                                       |
| **Phased**             | Deploying to regions/environments in stages (e.g., by country).                                   | Mitigates global outages.                                                                      | Complex coordination across teams.                                                              | Global applications with regional deployments.                                                   |
| **Database Migration** | Updating schema/data while minimizing user impact.                                               | Ensures data consistency.                                                                       | Risk of corruption if not handled carefully.                                                    | Database-driven applications (e.g., CRMs).                                                      |

---

## **Implementation Details**

### **1. Pre-Deployment Checklist**
Ensure **all** pre-deployment criteria are met before executing a rollout:
- **Code Review**: Approved by at least two team members.
- **Unit/Test Coverage**: ≥80% (or project-specific threshold).
- **Integration Tests**: Passed in staging.
- **Configuration Validation**: Environment variables, secrets, and settings verified.
- **Dependency Checks**: All libraries/versions compatible.
- **Backup**: Full database/application backup available.
- **Rollback Plan**: Automated rollback script tested.

### **2. Rollout Strategies**
#### **Blue-Green**
- **Steps**:
  1. Deploy new version to Green environment.
  2. Validate Green (performance, security, functionality).
  3. Switch traffic from Blue → Green (e.g., DNS flip or load balancer update).
  4. Keep Green active for rollback if needed.
- **Tools**: Kubernetes `BlueGreenDeployment`, AWS CodeDeploy, Docker swarm.

#### **Canary**
- **Steps**:
  1. Deploy new version alongside old.
  2. Route 5–10% traffic to new version.
  3. Monitor metrics (latency, errors).
  4. Gradually increase percentage until full rollout.
- **Tools**: Istio, Linkerd, or custom traffic shifters.

#### **Progressive Delivery**
- **Steps**:
  1. Deploy with feature flags disabled.
  2. Use a platform (e.g., LaunchDarkly) to toggle features for specific users.
  3. Gather metrics (e.g., engagement, crash rates).
  4. Expand to broader audiences.
- **Tools**: LaunchDarkly, Flagsmith, Unleash.

### **3. Rollback Procedures**
- **Automated Rollback**: Triggered by alerts (e.g., error spikes >3σ).
  ```bash
  # Example Kubernetes rollback command
  kubectl rollout undo deployment/my-app --to-revision=2
  ```
- **Manual Rollback**: Execute a pre-defined script (e.g., revert Git commit).
  ```bash
  git revert <last-commit>
  ```
- **Checklist**:
  - Confirm rollback triggered by actual failure (not false positives).
  - Verify old version is stable before promoting new version again.

### **4. Automation & CI/CD Integration**
- **GitOps**: Use tools like ArgoCD or Flux to sync Git repos with clusters.
- **CI/CD Pipelines**:
  ```yaml
  # Example GitHub Actions for Blue-Green
  jobs:
    deploy:
      steps:
        - name: Deploy Green
          run: kubectl apply -f green-deployment.yaml
        - name: Validate Green
          run: kubectl rollout status deployment/my-app --timeout=5m
        - name: Switch Traffic
          run: kubectl patch service/my-app -p '{"spec":{"selector":{"app":"green"}}}'
  ```

---

## **Query Examples**
### **1. Which technique minimizes downtime for a database update?**
**Answer**: **Blue-Green** (if schema changes allow parallel reads) or **Phased** (if regional).

### **2. How do I implement Canary with Kubernetes?**
```yaml
# Deployment with Canary annotation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  annotations:
    canary: "true"  # Label for traffic shifter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
---
# Service with weighted routing
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
  sessionAffinity: ClientIP
---
# Istio VirtualService for Canary
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app.example.com
  http:
    - route:
        - destination:
            host: my-app
            subset: v1  # Default (90%)
        - destination:
            host: my-app
            subset: v2  # Canary (10%)
          weight: 10
```

### **3. What’s the difference between Feature Flags and Canary?**
| **Feature Flags**       | **Canary**                                 |
|-------------------------|--------------------------------------------|
| Toggles features at runtime.  | Gradually exposes versions to users.        |
| Useful for experiments.   | Useful for stability testing.             |
| No traffic overhead.     | Requires monitoring infrastructure.         |

### **4. How do I design a rollback script for a database migration?**
```sql
-- PostgreSQL example
BEGIN;
-- Step 1: Revert schema changes
ALTER TABLE users DROP COLUMN IF EXISTS new_field;
-- Step 2: Revert data changes
UPDATE users SET status = 'active' WHERE status = 'trial';
-- Step 3: Rollback transaction (all changes undone if error)
ROLLBACK;
```

---

## **Related Patterns**
| **Pattern**               | **Connection to Deployment Techniques**                                                                 | **When to Use Together**                                                                          |
|---------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Infrastructure as Code** | Deployments rely on IaC templates (e.g., Terraform, CloudFormation) for consistency.                | When infrastructure must match deployment configurations.                                        |
| **Observability**         | Monitoring (Prometheus, Grafana) is critical for Canary/Progressive Deployment health checks.         | Always—deployments need real-time telemetry.                                                    |
| **Configuration Management** | Tools like Ansible or Chef manage runtime configurations post-deployment.                          | For dynamic environments (e.g., feature flags via Ansible).                                    |
| **Chaos Engineering**     | Simulates failures to test rollback procedures (e.g., Gremlin, Chaos Mesh).                       | Before production deployments to validate resilience.                                           |
| **Zero Trust Security**   | Ensures least-privilege access during deployments (e.g., temporary service accounts).              | For highly sensitive deployments (e.g., financial systems).                                      |

---
## **Further Reading**
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/) (Canary/Blue-Green).
- [Progressive Delivery Handbook](https://progresivedeployment.com/) (by Etsy).
- [AWS Well-Architected Deployment Best Practices](https://aws.amazon.com/architecture/well-architected/).