---
# **[Pattern] Zero-Downtime Deployment Reference Guide**

---

## **1. Overview**
The **Zero-Downtime Deployment** pattern ensures seamless application updates without causing service interruptions, minimizing user impact, and maximizing system availability. This pattern achieves this through concurrent operation of old and new application versions, gradual traffic redirection, and graceful failover mechanisms. Common use cases include web applications, microservices, and critical infrastructure where uptime is non-negotiable.

Key challenges addressed:
- **Minimizing user impact** by avoiding downtime during updates.
- **Handling application version conflicts** during transition.
- **Ensuring data consistency** during rollouts.
- **Managing failover** in case of deployment failures.

This guide covers implementation strategies, design considerations, and best practices for deploying applications without downtime.

---

## **2. Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                                                                                 | **Use Case Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Blue-Green Deployment** | Running two identical production environments (Blue & Green). Traffic switches between them during deployment.                                                                                                                                   | E-commerce platform switching from v1 (Blue) to v2 (Green) during Black Friday sales.                  |
| **Canary Deployment**     | Gradually routing a small percentage of traffic to the new version, monitoring, and scaling up if successful.                                                                                                                                    | SaaS platform testing a new feature with 1% of users before full rollout.                              |
| **Rolling Updates**       | Phased deployment across instances, updating one at a time with zero downtime.                                                                                                                                                                      | Kubernetes rolling updates for a 10-node application cluster.                                         |
| **Feature Flags**         | Conditionally enabling/disabling features without redeploying.                                                                                                                                                                                 | Enabling A/B testing for a new UI component in production.                                             |
| **Database Migration**    | Preparing a new database schema or schema changes in advance, ensuring backward/forward compatibility.                                                                                                                                     | Upgrading a PostgreSQL schema from v1 to v2 before deploying the new application version.              |
| **Health Checks**         | Endpoint checks to verify application readiness and signal readiness for traffic.                                                                                                                                                            | `/health` endpoint returning `200` before traffic is routed to a new instance.                         |
| **Circuit Breakers**      | Temporary traffic blocking if the new version fails, fall back to the old version.                                                                                                                                                              | Auto-reverting to v1 if v2 fails a load test with a 500 error spike.                                   |
| **Load Balancer**         | Distributing traffic across old/new versions until full rollout.                                                                                                                                                                               | AWS ALB routing 10% of traffic to v2, then increasing incrementally.                                  |

---

## **3. Implementation Schema**

Below is a reference schema for a **Zero-Downtime Deployment** implementation:

| **Component**            | **Role**                                                                                                                                                                                                                                                                 | **Example Tools/Technologies**                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Environment Setup**    | Maintain two identical production environments (Blue/Green or A/B).                                                                                                                                                                               | Kubernetes (namespaces), Docker Swarm, AWS EC2 Auto Scaling.                                               |
| **Traffic Routing**      | Use a load balancer to control traffic distribution between versions.                                                                                                                                                                          | Nginx, AWS ALB, Azure Load Balancer, Traefik.                                                              |
| **Deployment Orchestrator** | Automates deployment and traffic shifting (e.g., Kubernetes Deployments, FluxCD).                                                                                                                                                          | Kubernetes, ArgoCD, Jenkins, GitHub Actions.                                                              |
| **Database Layer**       | Supports backward/forward compatibility; may use feature flags for schema changes.                                                                                                                                                              | PostgreSQL (with logical replication), MongoDB (schema versioning), AWS RDS.                                |
| **Monitoring & Alerts**  | Real-time monitoring of health, performance, and errors during deployment.                                                                                                                                                                    | Prometheus, Grafana, Datadog, New Relic.                                                                  |
| **Rollback Mechanism**   | Automated or manual fallback to the previous version if issues arise.                                                                                                                                                                       | Blue-Green switch, Kubernetes `rollout undo`, feature flag toggles.                                      |
| **CI/CD Pipeline**       | Automates testing, staging, and deployment with zero-downtime checks.                                                                                                                                                                        | GitLab CI/CD, GitHub Actions, CircleCI, Argo Workflows.                                                   |
| **Feature Flags**        | Enables/disables features dynamically without redeployment.                                                                                                                                                                             | LaunchDarkly, Flagsmith, Unleash.                                                                          |

---

## **4. Implementation Steps**

### **Step 1: Prepare Environments**
- **Blue-Green Setup**:
  - Deploy a complete copy of the application in a separate environment (e.g., `blue` and `green`).
  - Ensure identical infrastructure, database, and dependencies.
- **Multi-Version Environment**:
  - Use Kubernetes namespaces or AWS Auto Scaling groups to host multiple versions simultaneously.

### **Step 2: Deploy the New Version**
- **Blue-Green**:
  - Deploy the new version to the `green` environment while `blue` remains active.
  - Validate the new version in staging (pre-production).
- **Canary/Rolling Updates**:
  - Deploy the new version in parallel with the old one.
  - Gradually shift traffic using:
    - **Percentage-based routing** (e.g., 10% → 50% → 100%).
    - **Headless service discovery** (e.g., Kubernetes `Service` with multiple `Pod` selectors).

### **Step 3: Traffic Shifting**
- **Blue-Green**:
  - Route all traffic to the `green` environment using a load balancer or DNS switch.
  - Example (AWS ALB):
    ```plaintext
    # Shift traffic from blue to green
    aws elbv2 modify-listener --listener-arn <listener-arn> \
        --default-actions type=instance,target-group-arn=<green-tg-arn>,weight=100
    ```
- **Canary**:
  - Use a feature flag service or load balancer rules to route a small percentage (e.g., 5%) to the new version.
  - Monitor metrics (e.g., error rates, latency) before scaling up.

### **Step 4: Database Considerations**
- **Schema Changes**:
  - Use backward-compatible migrations (e.g., adding columns, optional fields).
  - Example (PostgreSQL):
    ```sql
    -- Add a new column (backward-compatible)
    ALTER TABLE users ADD COLUMN new_field VARCHAR(255);
    ```
- **Data Migration**:
  - Run migrations during low-traffic periods or use double-write patterns.
  - Example (ETL job for schema changes):
    ```python
    # Pseudocode for data transformation
    def migrate_data(old_schema, new_schema):
        for record in old_schema.query().all():
            new_schema.insert(**record.as_dict())
    ```

### **Step 5: Monitoring & Validation**
- **Health Checks**:
  - Implement `/health`, `/ready`, and `/live` endpoints.
  - Example (Express.js):
    ```javascript
    app.get('/health', (req, res) => {
      res.status(200).json({ status: 'ok' });
    });
    ```
- **Metrics & Alerts**:
  - Monitor:
    - Error rates (e.g., `5xx` responses).
    - Latency percentiles (e.g., `p99`).
    - Throughput (e.g., requests/sec).
  - Alert on thresholds (e.g., `error_rate > 1%` → rollback).

### **Step 6: Rollback Plan**
- **Automated Rollback**:
  - Use CI/CD tools to revert to the previous version if metrics violate thresholds.
  - Example (ArgoCD Rollback):
    ```yaml
    # Sync policy in ArgoCD
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
        allowEmpty: false
    ```
- **Manual Rollback**:
  - Switch back to the old version via load balancer or DNS.
  - Example (Kubernetes):
    ```bash
    kubectl rollout undo deployment/my-app
    ```

### **Step 7: Finalize**
- Once the new version is fully validated:
  - Decommission the old environment (e.g., terminate `blue` instances).
  - Update documentation and rollback procedures.

---

## **5. Query Examples**

### **Kubernetes Rolling Update**
```bash
# Deploy new version with rolling update (replicas=3, max surge=1, max unavailable=0)
kubectl set image deployment/my-app my-app=my-image:v2 \
  --record \
  --rollback=true \
  --dry-run=client -o yaml | kubectl apply -f -
```

### **AWS ALB Canary Deployment**
```bash
# Create a canary target group (10% traffic)
aws elbv2 create-target-group \
  --name my-app-canary \
  --protocol HTTP \
  --port 80 \
  --target-type instance \
  --vpc-id vpc-123456 \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5

# Attach canary to ALB listener rule
aws elbv2 create-listener-rule \
  --listener-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-app/50d34... \
  --priority 1 \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-app-canary/1234567890abcdef \
  --conditions Field=host-header,Values=myapp.com,PathPattern=/api/v2
```

### **Database Migration Check**
```sql
-- Verify migration compatibility
SELECT * FROM information_schema.columns
WHERE table_name = 'users' AND column_name NOT IN ('email', 'created_at');
```

---

## **6. Best Practices**

1. **Gradual Rollouts**:
   - Start with a small percentage (e.g., 1%) of users or traffic.
   - Monitor for anomalies before scaling up.

2. **Automated Testing**:
   - Run integration tests and load tests in staging before production.
   - Example (Locust for load testing):
     ```python
     from locust import HttpUser, task, between

     class WebsiteUser(HttpUser):
         wait_time = between(1, 3)

         @task
         def load_new_version(self):
             self.client.get("/api/v2/endpoint")
     ```

3. **Feature Flags**:
   - Use feature flags to hide new features until fully tested.
   - Example (LaunchDarkly SDK):
     ```javascript
     const user = {
       key: 'user123',
       flags: {
         new_feature: true
       }
     };
     LD.init("YOUR_SDK_KEY", user);
     ```

4. **Database Optimization**:
   - Avoid blocking migrations; use non-blocking techniques (e.g., PostgreSQL `ALTER TABLE ... CONcurrently`).
   - Example:
     ```sql
     ALTER TABLE orders ADD COLUMN shipping_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00;
     ```

5. **Rollback Strategy**:
   - Document rollback steps (e.g., revert Docker images, switch load balancer rules).
   - Practice rollbacks in staging.

6. **Communication**:
   - Notify users/stakeholders of deployment windows (if applicable).
   - Example (Slack notification):
     ```json
     {
       "text": "🚀 New version (v2) deploying at 14:00 UTC. Canary testing started.",
       "attachments": [
         {
           "title": "Monitoring Dashboard",
           "title_link": "https://monitoring.example.com",
           "color": "#36a64f"
         }
       ]
     }
     ```

7. **Tooling**:
   - Use infrastructure-as-code (IaC) for reproducible environments (e.g., Terraform, Pulumi).
   - Example (Terraform for Blue-Green):
     ```hcl
     resource "aws_instance" "blue" { ... }
     resource "aws_instance" "green" { ... }

     resource "aws_lb_listener" "default" {
       load_balancer_arn = aws_lb.app.arn
       port              = 80
       protocol          = "HTTP"

       default_action {
         type             = "forward"
         target_group_arn = aws_lb_target_group.blue.arn
       }
     }
     ```

---

## **7. Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                                                                                             | **When to Use**                                                                                                                                                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Feature Toggle**               | Dynamically enable/disable features without redeploying.                                                                                                                                                                                                                         | Testing new features in production without affecting all users.                                                                                                                                                              |
| **Circuit Breaker**              | Temporarily stops traffic to a failing service.                                                                                                                                                                                                                               | Resilient microservices with potential cascading failures.                                                                                                                                                                     |
| **Database Sharding**            | Splits database load across multiple instances.                                                                                                                                                                                                                               | High-traffic applications needing horizontal scalability.                                                                                                                                                                     |
| **Retry Mechanism**              | Automatically retries failed requests with exponential backoff.                                                                                                                                                                                                               | Distributed systems with transient failures (e.g., network hiccups).                                                                                                                                                              |
| **Optimistic Locking**           | Prevents concurrent modifications by versioning records.                                                                                                                                                                                                                     | High-concurrency applications (e.g., inventory systems).                                                                                                                                                                        |
| **Microservices Architecture**  | Decomposes applications into small, independent services.                                                                                                                                                                                                                     | Large-scale applications requiring modular deployment.                                                                                                                                                                         |
| **Chaos Engineering**            | Intentionally fails components to test resilience.                                                                                                                                                                                                                           | Building robust, fault-tolerant systems.                                                                                                                                                                                     |

---

## **8. Troubleshooting**

| **Issue**                          | **Cause**                                                                                                                                                                                                                     | **Solution**                                                                                                                                                                                                                           |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **New version crashes on startup**  | Missing dependencies, misconfigured environment variables, or code errors.                                                                                                                                                              | Check logs (`kubectl logs pod/my-app-<pod>`), rollback, and fix in staging.                                                                                                                                                      |
| **Database schema mismatch**        | Old and new versions expect different schemas.                                                                                                                                                                                           | Run migrations in advance or use backward-compatible changes.                                                                                                                                                                     |
| **Load balancer misrouting**        | Incorrect target group or health check configuration.                                                                                                                                                                              | Verify ALB/TG rules (`aws elbv2 describe-target-group-attributes`), test health checks.                                                                                                                                    |
| **Feature flag not working**        | Misconfigured flag service or SDK.                                                                                                                                                                                                       | Check flag service logs (e.g., LaunchDarkly dashboard), verify user context.                                                                                                                                                          |
| **Slow rollout due to traffic**     | Insufficient capacity in the new version.                                                                                                                                                                                              | Increase replicas or use a phased rollout (e.g., 10% → 25% → ... → 100%).                                                                                                                                                       |
| **Rollback fails**                  | Database state mismatch or incomplete cleanup.                                                                                                                                                                                             | Run manual checks (e.g., `psql -c "\x ON; SELECT * FROM users LIMIT 10;"`), verify IaC state.                                                                                                                                |

---

## **9. Example Workflow (Canary Deployment)**

1. **Stage**:
   - Deploy `v2` to staging.
   - Run integration tests and load test with 100% traffic.
2. **Pre-Production**:
   - Deploy `v2` to a small canary group (e.g., 1% of users).
   - Monitor error rates and latency.
3. **Production**:
   - Gradually increase canary size (e.g., 1% → 5% → 20% → 100%).
   - If errors exceed threshold (e.g., `error_rate > 1%`), rollback.
4. **Finalize**:
   - Once stable, decommission old version (`v1`).

---
**Last Updated:** [Insert Date]
**Version:** 1.2