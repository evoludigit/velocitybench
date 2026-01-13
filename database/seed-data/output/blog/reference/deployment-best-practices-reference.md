**[Pattern] Deployment Best Practices – Reference Guide**

---

### **Overview**
Deploying applications safely and reliably minimizes downtime, reduces risks, and ensures consistency across environments. This guide outlines **Deployment Best Practices**, a pattern that standardizes deployment workflows, automates critical steps, and enforces checks to maintain operational stability. It covers **infrastructure-as-code (IaC), gradual rollouts, rollback strategies, monitoring, and security**—key pillars for production-grade deployments. Adhering to these practices reduces human error, accelerates recovery, and aligns with modern DevOps and SRE principles.

---

### **Key Concepts & Schema Reference**

| **Concept**               | **Definition**                                                                                     | **Key Components**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Infrastructure as Code** | Managing infrastructure (servers, networks, VMs) via version-controlled scripts (Terraform, CloudFormation). | IaC templates, state management tools (e.g., Terraform state files), secret management (Vault).     |
| **Blue-Green Deployment**  | Deploying a new version alongside the old one ("blue") and switching traffic ("green") to minimize downtime. | Load balancers, feature flags, canary release tools (e.g., Istio, Linkerd).                          |
| **Canary Releases**        | Gradually exposing a small subset of users to a new version to detect issues.                        | Traffic splitting (e.g., Kubernetes `WeightedRoute`), monitoring dashboards.                         |
| **Rollback Mechanism**     | Automated or manual process to revert to a previous stable version upon failure.                    | Health checks, deployment pipelines (e.g., Argo Rollouts), backup snapshots.                          |
| **Immutable Deployments** | Treating deployments as ephemeral; no in-place updates to containers/VMs.                          | Containerized applications, cloud-native deployments (e.g., Kubernetes pods), immutable AMIs.        |
| **Post-Deployment Checks** | Validating deployment success via automated tests (e.g., smoke tests, integration checks).          | CI/CD pipeline stages (e.g., GitHub Actions, Jenkins), health probes (e.g., `livenessProbe` in K8s). |
| **Security Hardening**     | Enforcing least-privilege access, encryption, and compliance checks.                              | IAM policies, secrets scanning (e.g., Snyk, Trivy), compliance-as-code (e.g., Open Policy Agent).    |
| **Observability**          | Real-time monitoring, logging, and tracing to diagnose issues.                                     | Logging tools (e.g., ELK Stack, Loki), metrics (e.g., Prometheus), APM (e.g., Datadog, Jaeger).       |

---

### **Implementation Details**

#### **1. Infrastructure as Code (IaC)**
**Purpose**: Ensure reproducibility, version control, and auditability of infrastructure.
**How to Implement**:
- Use **Terraform** or **AWS CloudFormation** to provision resources (e.g., EC2, RDS, S3).
- Store IaC templates in a **private Git repository** (e.g., GitHub, Bitbucket).
- **State Management**: Use remote backends (e.g., S3 + DynamoDB for Terraform) to track infrastructure state.
- **Secrets**: Integrate **HashiCorp Vault** or **AWS Secrets Manager** to avoid hardcoding credentials.
- **Compliance Checks**: Run **Terraform validate** and **TFLint** to catch misconfigurations early.

**Example Workflow**:
```bash
# Provision dev environment
terraform init
terraform plan -var-file="dev.tfvars"
terraform apply -var-file="dev.tfvars"

# Destroy after testing
terraform destroy -var-file="dev.tfvars"
```

---

#### **2. Blue-Green or Canary Deployments**
**Purpose**: Zero-downtime rollouts with minimal risk.
**Tools**: Kubernetes `Deployment`, Argo Rollouts, Istio, or service mesh traffic shifting.

**Blue-Green Example (Kubernetes)**:
```yaml
# Deploy "green" version alongside "blue" (active)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app
      version: green
  template:
    spec:
      containers:
      - name: app
        image: my-app:v2.0.0
---
# Update Service to route traffic to green
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    app: app
    version: green  # Switch from "blue" to "green"
```

**Canary Example (Argo Rollouts)**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: app-canary
spec:
  strategy:
    canary:
      steps:
      - setWeight: 20  # 20% traffic to canary
      - pause: {duration: 5m}
      - setWeight: 50
---
# Traffic is gradually shifted to the canary version.
```

---

#### **3. Rollback Strategies**
**Automated Rollback**:
- Use **health checks** (e.g., Kubernetes `livenessProbe`) to trigger rollbacks if metrics (e.g., error rate > 1%) exceed thresholds.
- Example: **Argo Rollouts** with autoscaling:
  ```yaml
  metrics:
  - name: requests
    threshold: 95
    interval: 1m
  ```

**Manual Rollback**:
- Store **backup snapshots** of databases (e.g., PostgreSQL `pg_dump`).
- Use **immutable infrastructure**: Re-deploy from a known-good version (e.g., `v1.x.y`).

---

#### **4. Immutable Deployments**
**Purpose**: Avoid configuration drift and simplify rollbacks.
**How to Apply**:
- **Containers**: Build images from a CI pipeline (e.g., GitHub Actions) and tag them (e.g., `v1.2.0`).
- **Servers/VMs**: Use **cloud-init** or **Packer** to create golden images.
- **Kubernetes**: Deploy new pods with updated images; delete old pods after verification.

**Example (CI Pipeline)**:
```yaml
# .github/workflows/deploy.yml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t my-app:${{ github.sha }} .
      - run: docker push my-app:${{ github.sha }}
      - run: kubectl set image deployment/app app=my-app:${{ github.sha }}
```

---

#### **5. Post-Deployment Checks**
**Automated Testing**:
- **Smoke Tests**: Verify basic functionality (e.g., HTTP 200 responses).
- **Integration Tests**: Test interactions with downstream services.
- **Load Testing**: Simulate traffic (e.g., **k6**, **Locust**) before full rollout.

**Example (Kubernetes Readiness Probe)**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
```

---

#### **6. Security Hardening**
**Pre-Deployment Checks**:
- **Scan Images**: Use **Trivy** or ** Clair** to detect vulnerabilities in container images.
  ```bash
  trivy image my-app:v2.0.0 --exit-code 1
  ```
- **Compliance**: Enforce policies with **Open Policy Agent (OPA)** or **kube-bench** for Kubernetes.

**Post-Deployment**:
- **Network Policies**: Restrict pod-to-pod communication (e.g., deny all by default).
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: deny-all
  spec:
    podSelector: {}
    policyTypes:
    - Ingress
    - Egress
  ```
- **Secrets Management**: Rotate credentials automatically (e.g., **AWS Secrets Rotation**).

---

#### **7. Observability**
**Logging**:
- Use **Fluentd** or **Loki** to aggregate logs.
- Example (EFK Stack):
  ```yaml
  # Deploy Elasticsearch, Fluentd, Kibana in Kubernetes.
  ```

**Metrics**:
- Deploy **Prometheus** with custom metrics (e.g., request latency, error rates).
  ```yaml
  - record: job:http_request_duration_seconds:summary{quantile="0.99"}
    expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job))
  ```

**Tracing**:
- Integrate **Jaeger** or **OpenTelemetry** for distributed tracing.
  ```python
  # Example OpenTelemetry SDK (Python)
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("process_order"):
      # Your code here
  ```

---

### **Query Examples**
The following queries can be used to validate deployment status or diagnose issues:

#### **1. Check Kubernetes Deployment Status**
```bash
kubectl get deployments --watch
```
**Expected Output**:
```
NAME     READY   UP-TO-DATE   AVAILABLE   AGE
app      2/2     2            2           5m
```

#### **2. Verify Traffic Shift in Canary Release**
```bash
kubectl describe rollout app-canary -n default
```
**Key Fields**:
- `canaryAnalysis`: Shows traffic distribution (e.g., `20% canary`, `80% stable`).

#### **3. Query Prometheus for Deployment Metrics**
```bash
kubectl exec -it prometheus-pod -- prometheus query 'rate(http_requests_total[5m]) by (job)'
```
**Output**:
```
{job="app"} 120.5
{job="app-canary"} 24.1  # 20% of traffic
```

#### **4. Inspect Rollback History (Argo Rollouts)**
```bash
kubectl get rollouts app-canary -o jsonpath='{.status.history}'
```

---

### **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Connection to Deployment Best Practices**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **[Infrastructure as Code]**     | Manages infrastructure via code.                                                                 | Underpins deployment consistency (e.g., Terraform for provisioning before deployment).                     |
| **[Canary Analysis]**             | Analyzes canary metrics to auto-approve/pause rollouts.                                           | Complements gradual rollouts by automating decisions based on observability data.                         |
| **[Progressive Delivery]**       | Gradually exposes features to users while monitoring impact.                                        | Enables safer deployments by reducing risk through incremental exposure.                                   |
| **[Chaos Engineering]**           | Proactively tests system resilience to failures.                                                    | Useful for validating rollback mechanisms and disaster recovery plans.                                      |
| **[Feature Flags]**               | Dynamically enables/disables features without redeploying.                                         | Allows A/B testing and safer deployments by decoupling code changes from user exposure.                   |

---
### **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| No automated rollback plan           | Define **health checks** and **rollback triggers** (e.g., error rate thresholds).               |
| Uncontrolled traffic shifts         | Use **canary analysis** to auto-pause if metrics degrade.                                          |
| Hardcoded secrets in IaC              | Integrate **Vault** or **Secrets Manager** for dynamic secrets.                                   |
| Lack of observability                | Deploy **Prometheus + Grafana** for metrics and **Loki** for logs.                                 |
| Configuration drift                  | Enforce **immutable deployments** (e.g., no manual edits to running containers).                  |

---
### **Further Reading**
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/)
- [Terraform Security Guide](https://learn.hashicorp.com/terraform/security)
- [Argo Rollouts Documentation](https://argo-rollouts.readthedocs.io/)
- [Google SRE Book – Deployment Best Practices](https://sre.google/sre-book/deployments/)

---
**End of Guide** | [Last Updated: MM/DD/YYYY]