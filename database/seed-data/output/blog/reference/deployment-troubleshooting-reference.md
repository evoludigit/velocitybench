# **[Pattern] Deployment Troubleshooting – Reference Guide**

---

## **Overview**
The **Deployment Troubleshooting** pattern provides a structured approach to diagnosing and resolving issues that arise during software deployments across environments (Dev, Staging, Production). It ensures minimal downtime by systematically identifying root causes, validating fixes, and preventing recurrence. This guide covers common failure scenarios, diagnostic methodologies, and best practices for post-mortem analysis. Use this pattern to iterate deployments, improve CI/CD reliability, and maintain system stability.

---

## **Key Concepts & Implementation Details**

### **1. Troubleshooting Stages**
Deployment issues are addressed in three sequential stages:

| **Stage**          | **Objective**                                                                 | **Key Actions**                                                                 |
|--------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Detection**      | Identify deployment failures                                                     | Review logs, monitor alerts, use observability tools (e.g., Prometheus, Datadog). |
| **Diagnosis**      | Root-cause analysis                                                           | Check rollback logs, compare pre/post-deployment states, analyze dependency issues. |
| **Remediation**    | Apply fixes and validate resolution                                             | Rollback or redeploy with adjustments; test in staging before production.      |
| **Post-Mortem**    | Document lessons learned and prevent recurrence                                 | Update runbooks, refine deployment strategies, and conduct blameless retrospectives. |

---

### **2. Common Failure Scenarios & Fixes**
Deployments can fail due to multiple factors. Below are categorized by environment and root cause:

#### **A. Rollout Failures**
| **Failure Type**       | **Root Cause**                                                                 | **Diagnostic Steps**                                                                 | **Fixes**                                                                                     |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **503/504 Errors**     | Backend service overload, misconfigured health checks, or DB connection issues | Check service metrics (latency, errors), verify load balancer logs, test DB connectivity. | Scale horizontally, adjust health check thresholds, retry DB connections with backoff.        |
| **Container Crashes**  | OOM kills, misconfigured resource limits, or missing environment variables   | Review Kubernetes (`kubectl describe pod`) or Docker logs (`docker logs`).              | Increase resource limits, validate environment variables, handle errors gracefully in code. |
| **DNS Resolution**     | Incorrect record propagation or misconfigured ingress routes                | Test DNS using `dig` or `nslookup`, verify ingress rules.                            | Update DNS TTL, correct ingress routes, or validate service discovery configuration.        |

#### **B. Configuration Drift**
| **Symptom**               | **Root Cause**                                                                 | **Diagnostic Steps**                                                                 | **Fixes**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Feature mismatches**    | Inconsistent config between environments (e.g., `settings.json` vs. Staging)  | Diff config files across environments, compare with Git history.                       | Use environment-specific config files, enforce config-as-code (e.g., Terraform, Ansible).   |
| **Permission errors**     | IAM roles, RBAC, or ACLs misconfigured                                         | Check IAM policies (`aws iam list-policies`), audit logs (e.g., CloudTrail).         | Adjust least-privilege principles, validate role assignments.                                 |

#### **C. Dependency Failures**
| **Symptom**               | **Root Cause**                                                                 | **Diagnostic Steps**                                                                 | **Fixes**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Vendor API downtime**   | External service SLA breaches or rate limits                                   | Monitor API status (e.g., `curl` endpoints, use uptime monitoring tools).             | Implement retries with exponential backoff, cache responses, or switch to a backup provider. |
| **Database schema mismatch** | Unapplied migrations or version mismatch                                       | Compare schema versions (`pg_dump --schema-only`), check migration logs.             | Run migrations manually, validate rollback scripts, or use schema migrations tools (e.g., Flyway). |

---

### **3. Diagnostic Tools**
| **Tool**               | **Purpose**                                                                 | **Usage Example**                                                                     |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Logging**            | Real-time error tracking                                                   | `grep "ERROR" /var/log/nginx/error.log \| tail -n 20`.                                |
| **Metrics**            | Performance and resource monitoring                                         | `kubectl top pods --namespace=<namespace>` (for K8s).                                 |
| **Tracing**            | Latency analysis (e.g., distributed transactions)                            | Use Jaeger or Zipkin to trace requests across services.                               |
| **Distributed Debugging** | Debug multi-container or microservice issues                               | `kubectl exec <pod> -- bash` for pod shells; use `nsenter` for network debugging. |
| **Infrastructure as Code (IaC) Audit** | Detect misconfigurations in deployments                                  | Run `terraform validate` or `ansible-lint` to check IaC files for errors.             |

---

## **Schema Reference**
Below are key schemas for deployment troubleshooting data structures:

### **1. Deployment Rollout Log Schema**
```json
{
  "deployment_id": "dpl-12345",
  "timestamp": "2024-05-20T14:30:00Z",
  "environment": "production",
  "status": "failed", // [successful, failed, rolled_back, pending]
  "reason": "OOM kill on pod-1234", // Free-text description
  "affected_services": ["api-gateway", "user-service"],
  "duration_seconds": 120,
  "rollback_strategy": "blue-green", // [blue-green, canary, rolling, immediate]
  "diagnostic_tags": [
    {"key": "error_type", "value": "container_crash"},
    {"key": "component", "value": "backend"}
  ],
  "related_incidents": ["inc-56789"] // Links to Jira/ServiceNow tickets
}
```

### **2. Failure Metrics Schema**
| Field               | Type         | Description                                                                 |
|---------------------|--------------|-----------------------------------------------------------------------------|
| `timestamp`         | ISO 8601     | When the failure was detected.                                              |
| `service_name`      | String       | Name of the impacted service (e.g., "auth-service").                        |
| `error_code`        | Integer      | HTTP status code or custom error ID (e.g., `500`, `DB_CONNECTION_FAILED`). |
| `latency_ms`        | Float        | Request latency at failure time.                                            |
| `error_count`       | Integer      | Number of failures in a given window.                                      |
| `component`         | String       | Layer affected (e.g., "database", "api", "cache").                          |

---
## **Query Examples**
Use these queries to analyze deployment failures via tools like **Prometheus**, **ELK Stack**, or **Grafana**.

### **1. Find Failed Deployments in the Last 24 Hours**
**PromQL:**
```promql
up{job="deployment"} == 0
  AND on() group_left
  time() - deployment_timestamp > 0
  AND deployment_timestamp > now() - 86400
```

**ELK Kibana Query:**
```
event.dataset: "deployment" AND
@timestamp: >now-24h AND
message: "STATUS: FAILED"
```

### **2. Identify Services with High Error Rates**
**Grafana Query (Prometheus):**
```promql
rate(http_requests_total{status=~"5.."}[1m])
  / rate(http_requests_total[1m])
  > 0.1  # >10% error rate
```

### **3. Detect Configuration Drift Between Environments**
**Terraform Command:**
```sh
terraform plan -out=tfplan && terraform show -json tfplan | jq '.planned_values.root_module.resources[] | select(.mode == "managed") | .address'
```
Compare outputs across environments for mismatches.

---

## **Related Patterns**
Deployments rely on other patterns for full observability and reliability. Refer to:

| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Observability](link)**        | Centralized logging, metrics, and tracing for real-time diagnostics.           | Always enable alongside deployments to detect issues early.                     |
| **[Canary Deployments](link)**   | Gradual rollouts to minimize impact                                             | High-traffic services where full rollouts risk downtime.                        |
| **[Blue-Green Deployments](link)** | Dual-environment switching for zero-downtime                                   | Critical systems where stability is paramount.                                 |
| **[Chaos Engineering](link)**    | Proactively test failure scenarios                                             | Post-deployment to validate resilience (e.g., failure injection tests).         |
| **[Infrastructure as Code](link)** | Version-controlled deployments                                                 | To avoid configuration drift and ensure reproducibility.                        |

---

## **Best Practices**
1. **Automate Detection**:
   - Use **SLOs (Service Level Objectives)** to trigger alerts for deviations.
   - Example: Alert if "p99 latency > 1s" persists for >5 minutes.

2. **Isolate Issues**:
   - Deploy to **staging-like production** (e.g., using **feature flags**) before production.
   - Use **circuit breakers** (e.g., Hystrix, Resilience4j) to prevent cascading failures.

3. **Document Everything**:
   - Maintain a **runbook** for common failures (e.g., "How to Rollback a K8s Deployment").
   - Example template:
     ```
     [Failure] Database connection timeout
     - **Steps**:
       1. Check DB instance health (`aws rds describe-db-instances`).
       2. Restart app pods (`kubectl rollout restart deploy/<app>`).
       3. Verify with `kubectl logs <pod>`.
     ```

4. **Blameless Post-Mortems**:
   - Focus on **systemic improvements**, not individual blame.
   - Example questions:
     - Could automated rollback have mitigated the issue?
     - Are our tests insufficient for this failure mode?

5. **Retest Deployments**:
   - After fixes, run **smoke tests** and **load tests** to validate stability.
   - Example smoke test script:
     ```bash
     #!/bin/bash
     curl -s -o /dev/null -w "%{http_code}" http://api.example.com/health | grep "200"
     ```

---
## **Glossary**
| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Rollback**       | Revert to a previously stable version of the application.                   |
| **Blue-Green**     | Deploying to a separate environment and switching traffic when stable.       |
| **Canary**         | Gradually exposing a new version to a subset of users.                        |
| **SLO**            | Service Level Objective (e.g., "99.9% uptime").                             |
| **Chaos Engineering** | Deliberately introducing failures to test resilience.                      |
| **Observability**  | Ability to understand system behavior via metrics, logs, and traces.        |

---
## **Further Reading**
- [Google SRE Book: Error Budgets](https://sre.google/sre-book/error-budgets/)
- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug/)
- [AWS Well-Architected Deployment Checklist](https://aws.amazon.com/architecture/well-architected/)