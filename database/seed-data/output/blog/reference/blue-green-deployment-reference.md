# **[Pattern] Blue-Green Deployment Reference Guide**

---

## **Overview**
Blue-Green Deployment is a **zero-downtime deployment strategy** that minimizes risk by maintaining two identical production environments:

- **Blue (Active):** Current stable version running live traffic.
- **Green (Standby):** New version, built before deployment, with identical infrastructure.

Traffic is switched en masse from **Blue → Green** via a feature flag or DNS/load balancer reroute. Upon validation (e.g., health checks), the old version (Blue) can be decommissioned. This reduces risk compared to traditional blueprint deployments (e.g., rolling updates) by isolating the new deployment.

*Key use cases:* Microservices, stateless applications, cloud-native deployments.

---

## **Implementation Details**

### **1. Core Components**
| **Component**       | **Description**                                                                 | **Example Tools**                          |
|---------------------|---------------------------------------------------------------------------------|--------------------------------------------|
| **Blue & Green Environments** | Fully cloned production-like environments (infrastructure, configurations). | Kubernetes namespaces, AWS EC2 instances   |
| **Traffic Director**  | Routes requests between Blue/Green via DNS, load balancer, or API gateway.      | Nginx, AWS ALB, Istio                     |
| **Feature Flags**    | Controls gradual rollout (optional).                                             | LaunchDarkly, Flagsmith                   |
| **Health Checks**    | Validates Green before full switch (CPU, latency, error rates).                 | Prometheus, custom endpoint checks        |
| **Database Sync**    | Ensures Green has identical data state (if stateful).                           | Database replication, changelogs          |
| **Rollback Plan**    | Automated cutoff (e.g., revert DNS to Blue) if Green fails post-switch.        | CI/CD pipeline hooks                       |
| **Monitoring**       | Real-time telemetry for traffic impact (e.g., APM tools).                       | Datadog, New Relic                         |

---

### **2. Deployment Workflow**
1. **Build Green Environment**
   Deploy the new version to Green, mirroring Blue’s infrastructure (e.g., same OS, dependencies).
   *Avoid:* Deploying to Green while Blue is live (prevents split traffic).

2. **Validate Green**
   - Run load tests/smoke tests.
   - Stress-test with 100% simulated traffic (if possible).

3. **Switch Traffic**
   - **Option A (Hard Cutover):** Instant DNS/load balancer update (all traffic → Green).
   - **Option B (Canary):** Gradually shift traffic (e.g., 10% → 90%) via feature flags.
   - Validate health metrics pre/post-switch.

4. **Decommission Blue**
   After confirmation, drain Blue (halt new requests) and decommission (optional).

5. **Monitor & Rollback (if needed)**
   - Automate rollback via CI/CD (e.g., failback to Blue if error rate spikes).
   - Example: `if (error_rate > 5%) { revert_traffic_to_blue() }`

6. **Repeat**
   Next deployment: Green becomes the new Blue; build a second Green.

---
### **3. Schema Reference**
| **Schema**            | **Description**                                                                 | **Example**                                  |
|-----------------------|---------------------------------------------------------------------------------|----------------------------------------------|
| **Environment Schema**| Defines identical resource configurations for Blue/Green.                        | `kubectl apply -f blue-green-config.yaml`     |
| **Traffic Switch Schema** | Rules for redirecting requests (e.g., host headers, path-based routing).     | `ALB Listener Rule: Host=*.green.example.com` |
| **Health Check Schema** | Defines thresholds for validation (e.g., <1% 5xx errors).                     | `Prometheus alert: alert(HighErrorRate)`      |
| **Database Schema**    | Ensures data consistency (e.g., read replicas, CDC tools).                       | `PostgreSQL logical replication`              |
| **Rollback Schema**    | Automated scripts to revert state (e.g., DNS record updates).                    | `Terraform destroy -target=load_balancer`     |

---

## **Query Examples**
### **1. Switch Traffic to Green (AWS ALB)**
```bash
# Update ALB listener rule to route traffic to Green targets
aws elbv2 modify-listener-rule \
  --listener-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/50ecd66f5c8c718f/ \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/green-tg/1234567890abcdef \
  --priority 1
```

### **2. Validate Blue-Green Sync (Database Check)**
```sql
-- Compare row counts between Blue and Green databases
SELECT
  COUNT(*) AS blue_rows,
  (SELECT COUNT(*) FROM green_db.table) AS green_rows
FROM blue_db.table;
```

### **3. Health Check Query (Prometheus)**
```promql
# Alert if Green fails health checks post-switch
up{env="green"} == 0
  OR http_request_duration_seconds{env="green"} > 2
```

### **4. Automated Rollback (CI/CD Pipeline)**
```yaml
# GitHub Actions example: Rollback if Green fails
name: Blue-Green Rollback
on: failure
jobs:
  revert:
    runs-on: ubuntu-latest
    steps:
      - name: Update DNS to Blue
        run: |
          aws route53 change-resource-record-sets \
            --hosted-zone-id Z1234567890 \
            --change-batch file://dns-revert.json
```

---

## **Requirements**
### **1. System Requirements**
| **Requirement**               | **Detail**                                  |
|-------------------------------|---------------------------------------------|
| **Infrastructure Duplication** | Blue/Green must be 100% identical.          |
| **Stateless Preference**      | Stateful apps need database sync tools.      |
| **Load Balancer/DNS Support**  | Must support rapid traffic redirection.     |
| **Observability**             | Metrics/logs for pre/post-validation.       |
| **Automated Rollbacks**       | CI/CD integration for failfast scenarios.   |

### **2. Example Architecture**
```
[Client] → [DNS/Load Balancer]
     ↓
[Blue (Active)] ←→ [Green (Standby)]
     ↑
[Shared Database (Replicated)]
```

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Canary Deployment**     | Gradient traffic shift (10% → 90%) rather than all-or-nothing.                 | High-risk changes, gradual validation.    |
| **Feature Flags**         | Dynamic enable/disable of features post-deploy.                               | A/B testing, phased rollouts.             |
| **Rolling Updates**       | Gradual pod replacement (e.g., Kubernetes).                                    | Stateless apps with lower risk tolerance. |
| **Shadow Deployment**     | Green processes requests but doesn’t serve them (observation-only).             | Zero-risk validation.                    |
| **Database Migration**    | Schema changes with zero downtime (e.g., GitHub’s migrate-to-master).        | Database schema updates.                 |

---

## **Best Practices**
1. **Test Green Independently**
   Load-test Green with 100% simulated traffic before switching.

2. **Database Sync**
   Use **bi-directional replication** or **changelogs** (e.g., AWS DMS) for stateful apps.

3. **Feature Flags for Rollback**
   Enable/disable features dynamically to isolate failures.

4. **Automate Rollbacks**
   Fail fast: Monitor post-switch and revert if metrics degrade (e.g., >5% errors).

5. **Document Rollback Steps**
   Include scripts for DNS/LB reverts in deployment documentation.

6. **Limit Blue-Green Scope**
   Avoid overloading Green with too many changes in one deployment.

7. **Use Immutability**
   Treat Green as disposable; rebuild it for each deployment.

---
**Note:** Blue-Green is ideal for **stateless** or **low-latency-tolerant** apps. For stateful apps, pair with database replication.