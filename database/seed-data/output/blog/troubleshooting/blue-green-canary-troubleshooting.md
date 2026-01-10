# **Debugging Blue-Green & Canary Deployments: A Troubleshooting Guide**

## **Introduction**
Blue-Green and Canary deployments reduce risk by gradually releasing changes to a subset of users. However, misconfigurations, traffic shifts, or hidden bugs can still cause failures. This guide helps diagnose and resolve common issues quickly.

---

## **Symptom Checklist**
Check these symptoms if deployments are failing:

✅ **Downtime during deployment**
- Traffic switch fails for >5 mins.
- Health checks return `5xx` errors during rollover.

✅ **Bug affects all users immediately**
- Traffic routing misconfigured (e.g., `50%` → `100%` unexpectedly).
- Canary group misdefined (e.g., wrong A/B test rules).

✅ **Slow rollback**
- Database migrations stuck, delaying rollback.
- Traffic routing stuck halfway (e.g., `nginx` misconfiguration).

✅ **Data loss or corruption**
- Unidirectional sync failures between DBs.
- Missing post-deployment validation checks.

---

## **Common Issues & Fixes**

### **1. Downtime During Traffic Switch**
**Symptom:**
- Service unavailable for minutes while switching between blue/green.
- Health checks return `5xx` errors.

**Root Causes:**
- **Load balancer misconfiguration** (e.g., `nginx`, `ALB`).
- **DNS propagation delays** (e.g., `CNAME` fails over).
- **Session affinity issues** (sticky sessions break).

**Fixes:**

#### **A. Check Load Balancer Health Checks**
- **Example (Nginx):**
  ```nginx
  upstream blue {
      zone blue 64k;
      server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
  }
  upstream green {
      zone green 64k;
      server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
  }
  ```
  **Debug:**
  ```bash
  curl -I http://<loadbalancer-ip>/health
  ```
  If `502 Bad Gateway`, check backend logs:
  ```bash
  journalctl -u <service> --no-pager | grep "502"
  ```

#### **B. Verify DNS Propagation**
- Use `dig` or `nslookup`:
  ```bash
  dig +short example.com
  ```
  If stale, force update:
  ```bash
  sudo systemd-resolve --flush-caches
  ```

#### **C. Disable Sticky Sessions**
- **Kubernetes:** Use `sessionAffinity: None` in `Service`.
- **AWS ALB:** Disable "Sticky Sessions" in ALB settings.

---

### **2. Bug Affects All Users Immediately**
**Symptom:**
- Traffic redirects from canary to blue/green incorrectly.

**Root Causes:**
- **Misconfigured traffic routing** (e.g., wrong weights).
- **Canary group misdefined** (e.g., wrong user/groups).

**Fixes:**

#### **A. Verify Traffic Split in API Gateway / Istio / ALB**
- **AWS ALB Canary:**
  ```json
  {
    "TargetGroups": [
      {
        "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/blue/abc123",
        "Weight": 50
      },
      {
        "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/green/def456",
        "Weight": 50
      }
    ]
  }
  ```
  **Debug:**
  ```bash
  aws elbv2 describe-load-balancer-attributes --load-balancer-arn <ALB_ARN>
  ```

#### **B. Check Canary Group Definitions**
- **Istio Canary:**
  ```yaml
  traffic:
    - route:
        - destination:
            host: service.default.svc.cluster.local
            subset: v2
      weight: 50
  ```
  **Debug:**
  ```bash
  kubectl get istioingressgateway -n istio-system
  kubectl logs -l istio=ingressgateway -n istio-system
  ```

---

### **3. Slow Rollback**
**Symptom:**
- Takes >30 mins to revert due to stuck rollback.

**Root Causes:**
- **Database migration locks** (e.g., `PostgreSQL` transactions).
- **Traffic routing stuck** (e.g., `nginx` not updating).

**Fixes:**

#### **A. Force Database Rollback**
- **PostgreSQL:**
  ```sql
  BEGIN;
  -- Revert migrations (e.g., DELETE from new_schema)
  ROLLBACK;
  ```
  **Debug:**
  ```bash
  psql -c "SELECT * FROM pg_locks;"
  ```

#### **B. Kill Stuck Load Balancer Updates**
- **AWS ALB:**
  ```bash
  aws elbv2 update-listener-rule-associations --listener-arn <arn> --associations <new-target-groups>
  ```

---

### **4. Data Loss During Rollback**
**Symptom:**
- Migrations can’t be undone, leading to corruption.

**Root Causes:**
- **Unidirectional replication** (e.g., `Master-Slave` without sync).
- **Missing pre-rollback checks**.

**Fixes:**

#### **A. Use Bidirectional Sync**
- **PostgreSQL:**
  ```bash
  pg_basebackup -h 10.0.0.2 -D /backups -U replicator -P
  ```
  **Debug:**
  ```bash
  postgres -c "SELECT * FROM pg_stat_replication;"
  ```

#### **B. Automate Pre-Rollback Validation**
- Example script to check DB consistency:
  ```bash
  #!/bin/bash
  if ! pg_isready -U postgres; then
    echo "DB not ready! Aborting rollback." >&2
    exit 1
  fi
  ```

---

## **Debugging Tools & Techniques**

### **1. Logs & Metrics**
- **ELK Stack:** Search for `deployment_failure` in logs.
- **Prometheus/Grafana:** Check `deployment_duration` metrics.

### **2. Network Traceroute**
```bash
mtr --report <service-url>
```
Look for packet loss indicating routing issues.

### **3. Automated Canary Analysis**
- Use **Flagger (Istio/Linkerd)** to auto-rollback if errors exceed threshold:
  ```yaml
  metrics:
  - name: requests
    thresholdRange:
      avg: 500
  ```

### **4. Blue-Green Deployment Checklist**
| Step | Action | Tool |
|------|--------|------|
| 1 | Verify backend health | `curl -I /health` |
| 2 | Check traffic routing | `aws elbv2 describe-target-health` |
| 3 | Validate DB sync | `pg_isready` |
| 4 | Log traffic split | Prometheus (`istio_requests_total`) |

---

## **Prevention Strategies**

1. **Automate Rollback Triggers**
   - Use **SLOs** (e.g., "If error rate > 1%, rollback").

2. **Test Traffic Switching in Staging**
   - Simulate 100% rollover before production.

3. **Use Feature Flags**
   - Enable/disable features independently of deployments.

4. **Database Replication Best Practices**
   - Always use **bidirectional sync** for critical services.

5. **Chaos Engineering**
   - Run **Gremlin/Chaos Mesh** to test failure scenarios.

---

## **Final Notes**
- **Blue-Green:** Fast switch (minutes), but requires full blue/green replicas.
- **Canary:** Slower rollout (hours), but safer for gradual risk assessment.

**Key Takeaway:** Always validate traffic routing, DB consistency, and rollback paths before production deployment.

---
**End of Guide** – Happy troubleshooting! 🚀