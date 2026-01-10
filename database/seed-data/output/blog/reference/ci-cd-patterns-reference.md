---

# **[Pattern] CI/CD Patterns for Backend APIs – Reference Guide**

---

## **1. Overview**
CI/CD (Continuous Integration/Continuous Deployment) automates the pipeline from code commit to production, ensuring rapid, reliable, and scalable releases for **backend APIs**. This pattern standardizes workflows for **testing, building, staging, and deploying** API changes while enforcing **consistency, traceability, and security**.

For backend APIs, CI/CD enables:
- **Frequent, low-risk deployments** (multiple times per day).
- **Automated regression testing** to catch integration issues early.
- **Canary releases** for gradual rollouts with rollback safety.
- **Infrastructure-as-code (IaC)** to manage environment consistency.

This guide covers **key CI/CD patterns**, their schema (mappings), and implementation considerations for REST/gRPC APIs.

---

## **2. Core CI/CD Patterns for Backend APIs**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Build & Test Pipeline** | Automate compilation, unit tests, and integration tests.                                             | Every code commit to catch early failures.                                                          |
| **Branch-Based Workflow** | Feature branches merge via Pull Requests (PRs) with gated checks (e.g., linting, tests).          | Collaborative teams needing code review and approval.                                                |
| **Canary Deployments**    | Gradually roll out changes to a small user subset to monitor performance.                           | High-traffic APIs where stability is critical.                                                      |
| **Blue-Green Deployments**| Switch between identical production copies (Blue/Green) via traffic routing.                         | Zero-downtime deployments for mission-critical APIs.                                                |
| **Feature Flags**         | Enable/disable API features dynamically without redeployment.                                        | A/B testing, gradual rollouts, or rolling back without downtime.                                     |
| **Infrastructure as Code**| Manage environments (K8s, cloud VMs) via YAML/Terraform scripts.                                     | Scalable, reproducible deployments across stages (dev → prod).                                     |
| **Post-Deploy Monitoring**| Track API health, latency, and errors in production via Prometheus/Grafana or cloud metrics.      | Proactively identify failures in real-time.                                                          |

---

## **3. Schema Reference**

### **3.1. Build & Test Pipeline Schema**
```json
{
  "stages": [
    {
      "name": "compile",
      "actions": ["run `go build ./...`", "validate dependencies"],
      "triggers": "on push to `main`"
    },
    {
      "name": "unit_tests",
      "actions": ["execute `go test ./...`", "store coverage in Artifactory"],
      "requirements": {
        "coverage_threshold": "80%",
        "fail_on_error": true
      }
    },
    {
      "name": "integration_tests",
      "actions": ["spin up test DB cluster via `docker-compose`"],
      "dependencies": ["unit_tests"],
      "timeout": "10 minutes"
    },
    {
      "name": "security_scan",
      "actions": ["run OWASP ZAP", "check for SQLi/XSS"],
      "optional": true
    }
  ]
}
```

---

### **3.2. Branch-Based Workflow Schema**
```json
{
  "branch_policies": {
    "main": {
      "protected": true,
      "require": ["PR from `feature/*`", "approval_by_2_owners"],
      "gated_checks": ["BuildSuccess", "TestCoverage80Plus"]
    },
    "feature/*": {
      "merge_strategy": "squash",
      "expiry": "60 days"
    }
  }
}
```

---

### **3.3. Canary Deployment Schema**
```json
{
  "environment": "production",
  "traffic_split": {
    "stable_version": 95%,
    "canary_version": 5%
  },
  "health_check": {
    "path": "/health",
    "timeout": "10s",
    "success_threshold": "99.9%"
  },
  "rollback_trigger": {
    "error_rate_threshold": 1.0%,
    "action": "switch_back_to_stable"
  }
}
```

---

### **3.4. Infrastructure-as-Code (IaC) Schema**
```yaml
# Terraform for Kubernetes cluster (simplified)
resource "kubernetes_deployment" "api" {
  metadata {
    name = "auth-api"
    labels = { app = "auth-service" }
  }
  spec {
    replicas = 3
    selector {
      match_labels = { app = "auth-service" }
    }
    template {
      spec {
        container {
          image = "registry.example.com/auth-service:${GIT_COMMIT_SHA}"
          ports {
            container_port = 8080
          }
        }
      }
    }
  }
}
```

---

## **4. Query Examples**
### **Query 1: List Failed Builds in a Branch**
```bash
# GitHub API
curl -H "Authorization: token YOUR_TOKEN" \
  "https://api.github.com/repos/OWNER/REPO/commits?sha=branch-name&per_page=100" \
  | jq '.commits[] | select(.statuses.state == "failure")'
```

### **Query 2: Check Canary Deployment Status**
```bash
# Prometheus Query
promql_query(1m, 'up{job="auth-api-canary"}')  # Check if canary pods are healthy
```

### **Query 3: Rollback to Last Stable Release**
```yaml
# Argo Rollout (K8s) Example
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: auth-api
spec:
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: "10m"}
      - setWeight: 50
      - pause: {duration: "20m"}
      - setWeight: 90
      - setWeight: 100
      - analysis:  # Rollback if error rate > 1%
        templates:
        - templateName: rollback-if-errors
```

### **Query 4: Feature Flag Toggle**
```bash
# LaunchDarkly CLI
ldflags set auth-service.feature_flag=true --env prod
```

---

## **5. Implementation Steps by Pattern**
### **5.1. Build & Test Pipeline**
1. **Tools**: GitHub Actions, GitLab CI, or Jenkins.
2. **Workflow**:
   - Lint code on PR (`golangci-lint`).
   - Run unit tests in parallel.
   - Deploy test images to a staging registry.
3. **CI/CD Tools**:
   - **Build**: `docker build -t auth-service:latest .`
   - **Test**: `pytest --cov=./` (Python) or `go test -cover` (Go).

### **5.2. Canary Deployment**
1. **Tools**: Istio, Argo Rollouts, or AWS CodeDeploy.
2. **Steps**:
   - Deploy new version alongside stable version.
   - Route 5% traffic via ingress rules.
   - Monitor metrics (e.g., `prometheus`).
3. **Rollback**:
   ```bash
   kubectl rollout undo deployment/auth-api  # K8s
   ```

### **5.3. Feature Flags**
1. **Tools**: LaunchDarkly, Unleash, or Flagsmith.
2. **Integration**:
   ```go
   // Check feature flag in Go
   flag, _ := client.BoolVariation(
       "auth-service.feature_flag",
       "user",  // key
       false,   // default
   )
   ```

---

## **6. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                                          | **Mitigation**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **No rollback plan**             | Extended downtime if deployment fails.                                                          | Use canary deployments with automatic rollback on failure.                                        |
| **Manual environment setup**     | Inconsistent staging/production.                                                                | Use IaC (Terraform, Pulumi) and blue-green deployments.                                          |
| **Skipping security scans**      | Vulnerabilities in production (e.g., CVE-2023-XXXX).                                             | Enforce OWASP ZAP/Trivy scans as part of the pipeline.                                            |
| **Long-lived feature branches** | Merge conflicts and stale code.                                                                  | Enforce branch expiry (e.g., 60 days) and PR merges via `rebase-merge`.                            |

---

## **7. Related Patterns**
| **Pattern Name**                     | **Description**                                                                                   | **When to Pair With**                                  |
|---------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **[API Versioning](link)**             | Manage gradual API changes without breaking clients.                                              | CI/CD for feature flags or canary deployments.        |
| **[Chaos Engineering](link)**          | Test resilience by injecting failures (e.g., pod kills).                                           | Post-deployment monitoring and canary releases.        |
| **[Event-Driven APIs](link)**          | Decouple services using events (Kafka, RabbitMQ).                                                 | CI/CD for event-processing microservices.               |
| **[Observability Stack](link)**       | Centralized logs/metrics/tracing (ELK, OpenTelemetry).                                           | Post-deploy monitoring for canary/blue-green deploys.   |
| **[Security Testing in CI](link)**    | Automate SAST/DAST scans (e.g., SonarQube) in the pipeline.                                      | Build & test stages for backend APIs.                   |

---

## **8. Key Metrics to Track**
| **Metric**                     | **Tool**               | **Threshold**               |
|----------------------------------|-------------------------|------------------------------|
| Test coverage                    | Cobertura, JaCoCo       | ≥ 80%                        |
| Deployment frequency             | CI/CD dashboard (JIRA) | ≥ 5/day                      |
| Mean Time to Detect (MTTD)       | Prometheus alerts       | < 5 minutes                  |
| Error rate in canary             | Grafana dashboard       | < 1%                         |
| Rollback rate                    | CI/CD logs              | < 0.1%                       |

---

## **9. Example CI/CD Pipeline (GitHub Actions)**
```yaml
name: Auth API CI/CD
on: [push]
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: "1.21"
      - name: Run tests
        run: |
          go test -v ./... -coverprofile=coverage.out
          go tool cover -func=coverage.out
      - name: Build Docker image
        run: docker build -t auth-service:${{ github.sha }} .
      - name: Push to Registry
        run: docker push registry.example.com/auth-service:${{ github.sha }}
```

---
**Note**: Replace placeholders (`YOUR_TOKEN`, `registry.example.com`) with actual values. Always validate tooling versions for compatibility.