---
**# [Pattern] Availability Migration Reference Guide**

---

## **1. Overview**
**Availability Migration** is a pattern used to *seamlessly transition service availability* across environments (e.g., dev → staging → production) with minimal downtime or disruption. This pattern ensures workloads run continuously during transitions by leveraging **blue-green deployments**, **canary releases**, or **traffic shifting**, reducing risk while maintaining high availability.

Target use cases:
- Zero-downtime deployments for critical applications.
- Gradual rollout of updates to validate stability.
- Migration of workloads to new infrastructure (e.g., Kubernetes clusters, cloud regions).
- Chaos engineering simulations without service interruption.

---

## **2. Implementation Details**

### **Core Concepts**
| Concept               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Blue-Green**        | Maintain two identical production environments (Blue/Green). Traffic is shifted between them.   |
| **Canary Release**    | Roll out updates to a small subset of users first, then gradually expand.                       |
| **Traffic Splitting** | Route requests between old/new versions using weights (e.g., 90% old, 10% new).                |
| **Circuit Breaker**   | Temporarily halt traffic to a faulty service to prevent cascading failures.                     |
| **Feature Flags**     | Enable/disable features dynamically at runtime, decoupled from deployment.                    |
| **Rollback Plan**     | Automated or manual reversal to the previous version if issues arise.                          |

### **Key Components**
| Component            | Purpose                                                                                         |
|----------------------|-------------------------------------------------------------------------------------------------|
| **Load Balancer**    | Distributes traffic between environments (e.g., AWS ALB, NGINX).                              |
| **Service Mesh**     | Manages traffic routing, retries, and observability (e.g., Istio, Linkerd).                   |
| **Configuration Mgmt**| Centralized config (e.g., Consul, Kubernetes ConfigMaps) to sync settings across environments. |
| **Monitoring**       | Real-time metrics (Prometheus, Grafana) and alerting to detect anomalies during migration.    |
| **CI/CD Pipeline**   | Automates testing/deployment (e.g., GitHub Actions, ArgoCD) before cutting over traffic.       |

---

## **3. Schema Reference**

### **A. Blue-Green Deployment Schema**
| Field               | Type         | Description                                                                                     | Example Value                          |
|---------------------|--------------|-------------------------------------------------------------------------------------------------|----------------------------------------|
| `environment`       | String       | Current active environment ("blue" or "green").                                               | `"blue"`                               |
| `traffic_weight`    | Integer      | Percentage of traffic routed to the secondary environment (0–100).                             | `10` (10% to green)                    |
| `health_check_url`  | String       | Endpoint to verify service health.                                                             | `/health`                              |
| `rollover_timeout`  | Duration     | Max time to complete traffic shift (e.g., 5m).                                                | `PT5M`                                 |
| `rollback_trigger`  | Boolean      | Automatically roll back if health checks fail.                                               | `true`                                 |
| `environment_vars`  | Object       | Config overrides per environment (e.g., `DB_HOST`).                                           | `{ "DB_HOST": "db-green.example.com" }` |

---

### **B. Canary Release Schema**
| Field               | Type         | Description                                                                                     | Example Value                          |
|---------------------|--------------|------------------------------------------------------------------------------------------------|----------------------------------------|
| `canary_percentage` | Integer      | % of users/traffic routed to canary.                                                          | `5`                                     |
| `user_groups`       | Array        | Specific user segments for canary testing (e.g., `["dev-team"]`).                              | `["alpha-testers"]`                    |
| `feature_flags`     | Array        | Flags toggled for canary (e.g., `["new-ui"]`).                                                 | `["experimental-auth"]`               |
| `monitoring_rules`  | Object       | Alerting thresholds (e.g., `error_rate > 1%`).                                               | `{ "latency": { "threshold": "P99 < 500ms" } }` |
| `staging_duration`  | Duration     | Time canary runs before full rollout (e.g., 1h).                                              | `PT1H`                                 |

---

### **C. Traffic Shifting Schema**
| Field               | Type         | Description                                                                                     | Example Value                          |
|---------------------|--------------|------------------------------------------------------------------------------------------------|----------------------------------------|
| `service_version`   | String       | Identifier for the target version (e.g., `v2.1.0`).                                             | `"v2.1.0-canary"`                      |
| `destination`       | String       | Target environment (e.g., `us-west-2`).                                                      | `"production-green"`                   |
| `headers`           | Object       | Custom headers for routing (e.g., `X-Canary: true`).                                          | `{ "X-User-Group": "beta" }`           |
| `retries`           | Integer      | Max retries for failed requests.                                                               | `3`                                     |
| `timeout`           | Duration     | Request timeout (e.g., 30s).                                                                | `PT30S`                                |

---

## **4. Query Examples**

### **A. Blue-Green Traffic Shift (Terraform/CloudFormation)**
```hcl
# AWS ALB configuration to shift traffic from Blue to Green
resource "aws_lb_listener" "blue_to_green" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.green.arn # Shift 0% initially
    weighted_routing_policy {
      weight             = var.traffic_weight # 10% to Green
      target_group_index = 1
    }
  }
}
```

### **B. Canary Release (Kubernetes Ingress)**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: canary-ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-v1
            port:
              number: 80
        # Route 5% of traffic to canary
        canary:
          service: app-v2
          weight: 5
```

### **C. Feature Flag Migration (LaunchDarkly)**
```json
{
  "key": "new-auth-flow",
  "version": 1,
  "on": false,
  "targets": [
    { "key": "dev-team", "variation": 1, "weight": 100 }
  ],
  "rules": [
    { "variation": 1, "clients": ["web", "mobile"] }
  ]
}
```

### **D. Rollback Trigger (Prometheus Alert)**
```yaml
groups:
- name: canary-failure
  rules:
  - alert: CanaryErrorRateHigh
    expr: rate(http_requests_total{service="app", status=~"5.."}[5m]) / rate(http_requests_total{service="app"}[5m]) > 0.01
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Canary release {{ $labels.service }} has error rate >1%. Rolling back..."
      runbook_url: "https://runbooks.example.com/canary-failures"
```

---

## **5. Related Patterns**

| Pattern                  | Description                                                                                     | When to Use                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Strangler Fig**        | Gradually replace legacy systems by wrapping them with new services.                          | When refactoring monolithic apps incrementally.                                                |
| **Circuit Breaker**      | Fail fast and avoid cascading failures during migrations.                                     | When dependent services are unreliable.                                                        |
| **Feature Toggles**      | Enable/disable features independently of deployments.                                         | For A/B testing or staged rollouts.                                                           |
| **Database Migration**   | Synchronize databases across environments with minimal downtime.                              | When schema changes or data migrations are required.                                           |
| **Chaos Engineering**    | Test resilience by injecting failures (e.g., killing pods).                                   | To validate availability migration plans.                                                      |
| **Multi-Region Deployment** | Deploy to multiple availability zones/cloud regions for redundancy.                          | For global applications with low-latency requirements.                                         |

---

## **6. Best Practices**
1. **Gradual Rollouts**: Start with **<5% traffic** for canaries, monitor, then expand.
2. **Automated Health Checks**: Use liveness/readiness probes to detect failures early.
3. **Rollback Readiness**: Design rollback scripts/pipelines *before* migration.
4. **Observability**: Track metrics (latency, error rates) and logs in real-time.
5. **Document Rollback Steps**: Clearly document manual intervention needed for failures.
6. **Security**: Validate certificates, IAM policies, and network security groups before shifting traffic.
7. **User Communication**: Notify users of changes (e.g., "We’re running a canary update—expect minor bugs").

---
**# End of Reference Guide** (Word count: ~1,100)