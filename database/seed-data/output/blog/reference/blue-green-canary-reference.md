# **[Pattern] Blue-Green Deployments & Canary Releases: Reference Guide**

---

## **Overview**
Blue-green deployments and canary releases are **zero-downtime** strategies that minimize risk during application updates. Unlike traditional deployments—which replace the old version abruptly—these methods balance **performance**, **scalability**, and **resilience** by gradually shifting traffic.

- **Blue-Green Deployment**: Runs two identical production environments side-by-side (Blue and Green). Traffic is switched between them with minimal downtime.
- **Canary Release**: Gradually routes a small percentage of traffic to a new version to detect issues before full rollout.

Both patterns enable **fast rollback** if anomalies occur, ensuring system stability.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Use Case**                                                                 | **Example**                          |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------|
| **Blue-Green Environments** | Two identical production environments (Blue & Green) with identical data.    | Deployments where downtime must be avoided (e.g., e-commerce).              | Switching all traffic from Blue to Green. |
| **Canary Traffic**     | A small subset of users routed to the new version.                          | Testing before full rollout (e.g., bug detection).                         | 5% of users see the new app version. |
| **Rollback Mechanism** | Instant traffic switchback to the previous version if errors occur.          | Mitigating failures (e.g., API crashes, UI breaks).                        | Revert to Blue if Green fails.       |
| **Feature Flags**      | Toggle new features on/off dynamically for targeted testing.                  | A/B testing or gradual feature rollouts.                                    | Enable new checkout flow for 1% users. |

---

## **Implementation Schema**
### **1. Blue-Green Deployment**
| **Component**       | **Description**                                                                 | **Configuration Example**                                                                 |
|---------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Environment Setup** | Two identical environments (Blue & Green) with the same infrastructure.        | AWS: `BlueEC2Cluster` → `GreenEC2Cluster`; Kubernetes: `blue-namespace` → `green-namespace` |
| **Traffic Switching** | Uses a **load balancer** (L7/L4) or **DNS-based routing** to redirect traffic. | NGINX: `switch_to_green()`; AWS ALB: Update target group weights.                         |
| **Data Synchronization** | Databases must be consistent between environments (e.g., replication).      | PostgreSQL: Logical replication; DynamoDB: Multi-active regions.                          |
| **Rollback Trigger**  | Automated checks (e.g., error rates, latency) or manual intervention.      | CloudWatch Alarms: If `ErrorRate > 5%`, switch back to Blue.                            |

### **2. Canary Release**
| **Component**       | **Description**                                                                 | **Configuration Example**                                                                 |
|---------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Canary Group**    | A subset of users (e.g., 1-10%) routed to the new version.                     | Istio: `CanaryRoute` with `trafficSplit: 5%`.                                         |
| **Gradual Ramp-Up** | Gradually increase canary traffic (e.g., +5% every 15 mins).                  | Kubernetes: `HorizontalPodAutoscaler` for new pods.                                    |
| **Monitoring**      | Real-time metrics (e.g., errors, session duration) to detect issues.           | Prometheus + Grafana: Alert if `new_version_error_rate > old_version`.                 |
| **Full Rollout**    | If stable, shift remaining traffic to the new version (e.g., 100% to Green). | Terraform: Update `ALB` listener rule to route all traffic to Green.                     |

---

## **Query Examples**

### **1. Blue-Green Deployment Workflow**
#### **Pre-Deployment**
```bash
# Deploy new version to Green environment
kubectl apply -f green-deployment.yaml --namespace=green

# Verify Green is healthy (e.g., via Prometheus)
curl http://green-service:8080/health | grep "OK"
```
#### **Traffic Switch**
```bash
# Update ALB target group weights (AWS CLI)
aws elbv2 update-target-group-weights --target-group-arn tg-blue --weights '{"Blue":50,"Green":50}'

# Or use Kubernetes Ingress (NGINX)
kubectl apply -f ingress-canary.yaml
```
#### **Rollback**
```bash
# Revert to Blue if issues detected
aws elbv2 update-target-group-weights --target-group-arn tg-green --weights '{"Green":0}'
```

---

### **2. Canary Release Workflow**
#### **Deploy Canary Version**
```bash
# Deploy new version as canary (sidecar injection via Istio)
kubectl annotate deployment app-v2 istio-injection=enabled
kubectl apply -f canary-deployment.yaml

# Configure traffic split (10% canary)
kubectl apply -f canary-virtualservice.yaml
```
#### **Monitor & Scale**
```bash
# Check canary metrics (Prometheus)
curl http://prometheus:9090/graph?query=up{namespace="green"}

# Scale canary up (if stable)
kubectl scale deployment app-v2 --replicas=10
```
#### **Full Rollout**
```bash
# Remove canary flag and shift 100% to new version
kubectl patch virtualservice app -p '{"spec":{"http":{"-[route]","-":"*"}}}'
```

---

## **Rollback Scenarios**
| **Scenario**               | **Action**                                                                                     | **Tools/Commands**                                                                       |
|----------------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **High Error Rate**        | Switch back to previous version.                                                               | AWS: `aws elbv2 update-target-group-weights --weights '{"Blue":100}'`                   |
| **Performance Degradation** | Reduce canary traffic or pause rollout.                                                     | Istio: Adjust `trafficSplit` (e.g., `--weights '{"Blue":95,"Green":5}'`)                |
| **Database Sync Failure**  | Revert and resolve replication issues before retrying.                                       | PostgreSQL: `pg_basebackup --format=p --host=blue-db --port=5432 --slot=green`         |
| **Infrastructure Outage**  | Use disaster recovery backup (e.g., snapshot).                                               | Terraform: `terraform apply -auto-approve` (restore from backup state)                 |

---

## **Tools & Technologies**
| **Category**       | **Tools**                                                                                   | **Use Case**                                                                             |
|--------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Orchestration**  | Kubernetes, Docker Swarm, AWS ECS                                                         | Deploy and manage Blue-Green environments.                                              |
| **Load Balancing** | NGINX, AWS ALB, Istio, Linkerd                                                           | Route traffic between Blue/Green or canary groups.                                       |
| **Monitoring**     | Prometheus, Grafana, Datadog, New Relic                                                   | Track error rates, latency, and user impact.                                             |
| **CI/CD Pipelines**| Jenkins, GitHub Actions, GitLab CI, ArgoCD                                                 | Automate canary deployments and rollbacks.                                               |
| **Database**       | PostgreSQL (logical replication), DynamoDB (multi-region), MongoDB (sharding)            | Keep Blue/Green databases in sync.                                                       |
| **Feature Flags**  | LaunchDarkly, Flagsmith, Unleash                                                          | Dynamically enable/disable features in canary releases.                                  |

---

## **Best Practices**
1. **Testing Before Production**
   - Run **load tests** (e.g., Locust, JMeter) on canary environments before full rollout.
   - Use **staging environments** that mirror production (e.g., same database schema).

2. **Monitoring & Alerts**
   - Set up **SLOs (Service Level Objectives)** for latency, error rates, and success rates.
   - Example alert (Prometheus):
     ```yaml
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "Canary release {{ $labels.instance }} has 10%+ errors"
     ```

3. **Database Considerations**
   - Use **read replicas** for Blue-Green to avoid write conflicts.
   - For event-driven apps, use **Kafka/Pulsar** with consumer groups to sync data.

4. **Gradual Rollout**
   - Start with **1-5% canary traffic** and monitor for **1-2 hours** before scaling.
   - Example ramp-up schedule:
     ```
     Time   | Canary %
     -------------------
     0m     | 1%
     30m    | 5%
     1h     | 10%
     2h     | 20%
     4h     | 50%
     ```

5. **Documentation**
   - Maintain a **rollout checklist** for teams (e.g., pre-flight checks, monitoring targets).
   - Use **runbooks** for common failure scenarios (e.g., "How to roll back canary due to API timeout").

---

## **Failure Modes & Mitigations**
| **Failure Mode**               | **Root Cause**                                                                 | **Mitigation**                                                                          |
|--------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Traffic Switch Failure**     | Load balancer misconfiguration or downtime.                                    | Use **multi-region load balancers** (e.g., AWS Global Accelerator).                    |
| **Database Desync**            | Replication lag or failed sync during deploy.                                   | Enable **bi-directional replication** or use **conflict-free replicated data types (CRDTs)**. |
| **Canary Drift**               | Canary group differs from production traffic (e.g., different devices/geos). | Use **user-based canary selection** (e.g., `/v1/canary?user_id=123`).                |
| **Cold Start Latency**         | New version pods not warmed up.                                                | Pre-warm pods before traffic shift (e.g., `kubectl rollout restart deployment app`).   |
| **Monitoring Blind Spot**      | Missing metrics for canary-specific errors.                                    | Extend monitoring to **canary-only dashboards** (e.g., "Green metrics" in Grafana).   |

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                           |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **[Feature Toggles](https://microservices.io/patterns/feature-toggle.html)** | Enable/disable features dynamically for targeted testing.                                      | Gradually roll out features without deploying new versions.                            |
| **[Progressive Delivery](https://www.progressivedelivery.com/)** | Combines canary releases with **A/B testing** and **shadow releases**.                          | Experiment with new UIs/APIs without user impact.                                      |
| **[Chaos Engineering](https://chaosengineering.io/)** | Intentionally inject failures to test resilience.                                             | Validate Blue-Green/Canary rollback procedures.                                        |
| **[Blue-Green Testing](https://www.thoughtworks.com/radar/techniques/blue-green-deployment)** | Test new versions in Blue before switching to Green.                                     | Verify end-to-end functionality before production cutover.                              |
| **[Dark Launching](https://signalvnoise.com/posts/3194-dark-launching-your-feature)** | Deploy new features to 0% of users; enable via toggles.                                        | Test features in production without user disruption.                                  |

---

## **Example Architecture**
```plaintext
┌───────────────────────────────────────────────────────────────────────────────┐
│                                Production Traffic                          │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────────┤
│    DNS/LB       │   Blue (v1)     │   Green (v2)   │   Canary Group (5%)     │
│ (Route53/ALB)   │ (95% traffic)   │ (5% traffic)   │ (Subset of users)         │
├─────────┬───────┼─────────┬───────┼─────────┬───────┼───────────────────────────┤
│         │         │         │         │         │                         │
│  Users  │         │         │         │         │                         │
└─────────┴─────────┴─────────┴─────────┴─────────┘                         │
                                  │                                           │
                                  ▼                                           │
┌───────────────────────────────────────────────────────────────────────────┐
│                           Monitoring & Alerts                           │
│  - Prometheus + Grafana (metrics)                                       │
│  - SLOs for latency/error rates                                        │
│  - Automated rollback on failure                                     │
└───────────────────────────────────────────────────────────────────────────┘
```

---
**Keywords**: Blue-Green, Canary Release, Zero-Downtime, Feature Flags, Progressive Delivery, Resilience.