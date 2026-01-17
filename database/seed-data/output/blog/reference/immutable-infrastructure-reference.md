---
# **[Pattern] Immutable Infrastructure Reference Guide**

---

## **Overview**
Immutable Infrastructure is a DevOps and cloud-native pattern where **servers, containers, or virtual machines (VMs) are never modified after deployment**. Instead of patching, updating, or reconfigured existing instances, new, identical, and pre-validated versions are deployed alongside (or replacing) the old ones. This eliminates drift, simplifies rollbacks, and ensures consistency by enforcing strict version control and automated rebuilds.

Key principles include:
- **Statelessness**: All data is externalized (e.g., databases, storage, configs via secrets/vaults).
- **Pre-commit Validation**: Deployments only occur after rigorous testing (CI/CD pipelines).
- **Automated Replacement**: Failed or outdated instances are terminated and replaced.
- **Horizontal Scaling**: New instances are spun up to handle traffic, not patched in-place.

This pattern is widely adopted in **containerized environments (Docker, Kubernetes), serverless architectures, and cloud-native deployments** (AWS, GCP, Azure).

---

## **Schema Reference**
Below is a standardized schema for implementing Immutable Infrastructure, categorized by **Infrastructure-as-Code (IaC) layers**, **Deployment Strategies**, and **Validation Mechanisms**.

| **Category**               | **Component**               | **Description**                                                                                                                                                                                                 | **Tools/Technologies**                                                                                     |
|----------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Infrastructure Layer**   | Stateless Design             | All working directories, user data, and configs are stored externally (e.g., S3, EFS, ConfigMaps).                                                                                                       | Docker, Kubernetes ConfigMaps/Secrets, AWS EFS, Terraform `external_data`                          |
|                            | Containerization            | Applications packaged in immutable containers with minimal, fixed dependencies.                                                                                                                             | Docker, Buildpacks, Multi-stage Dockerfiles, Kaniko (for builds inside Kubernetes)                   |
|                            | Image Registry               | Pre-built, versioned container/images (e.g., `app:v1.2.0`) stored in a registry (e.g., ECR, Harbor).                                                                                                      | Docker Registry, Google Container Registry, AWS ECR                                                     |
| **Deployment Layer**       | CI/CD Pipeline               | Automated builds, tests, and artifact promotion (e.g., `dev` → `prod`) with rollback capability.                                                                                                        | GitHub Actions, GitLab CI, Jenkins, ArgoCD, Flux, Tekton                                         |
|                            | Deployment Strategies        |                                                                                                                                                                                                                 |                                                                                                         |
|                            |                              | **Blue-Green**                     | Parallel live environments; traffic shifted via routing (e.g., AWS ALB, Istio).                                                                                                               | Kubernetes `RollingUpdate`, AWS CodeDeploy, Traefik                                             |
|                            |                              | **Canary**                         | Gradual traffic shift to new version (e.g., 10% → 100%).                                                                                                                                           | Istio, Flagger, Kubernetes `WeightedRouting`                                                  |
|                            |                              | **Shadow Traffic**                | New version runs alongside old without serving live traffic (metrics compared).                                                                                                                         | Envoy, Linkerd, custom service mesh                                                               |
|                            |                              | **Blue-Green with Feature Flags**  | Dynamic feature toggles enable incremental rollouts.                                                                                                                                                   | LaunchDarkly, Unleash, Kubernetes `CanaryAnalysis`                                             |
| **Validation Layer**       | Pre-Deployment Tests         | Unit, integration, and security tests (e.g., SAST, DAST) run against the new image.                                                                                                                          | SonarQube, OWASP ZAP, Trivy, Kubernetes `Job`                                                        |
|                            | Health Checks                | Liveness/readiness probes validate instance health before traffic exposure.                                                                                                                               | Kubernetes `LivenessProbe`, AWS ELB health checks, Prometheus                                   |
|                            | Rollback Triggers            | Automatic or manual rollback if errors exceed thresholds (e.g., error rate > 5%).                                                                                                                            | Prometheus + Alertmanager, AWS CloudWatch Alarms, Istio `CanaryAnalysis`                          |
| **Operations Layer**       | Logging & Monitoring         | Centralized logs/metrics for all instances (no local storage).                                                                                                                                         | ELK Stack, Loki + Promtail, AWS CloudWatch, Datadog                                              |
|                            | Secrets Management           | Secrets injected at runtime (never hardcoded).                                                                                                                                                           | HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets, AWS Parameter Store                     |
|                            | Instance Lifecycle           | Old instances terminated when no longer needed (e.g., after 5 minutes of idle).                                                                                                                              | Kubernetes `TTLController`, AWS Auto Scaling, Kubernetes `PodDisruptionBudget`                 |

---

## **Query Examples**
### **1. Deploying an Immutable Container with Kubernetes**
**Scenario**: Deploy a new version (`v1.3.0`) of an app using a **Blue-Green** strategy.

```yaml
# deployment-blue-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 2
  strategy:
    type: ReplicaSet  # Ensures zero downtime
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
        version: v1.3.0  # Tagged for canary/blue-green
    spec:
      containers:
      - name: web
        image: registry.example.com/app:v1.3.0
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 3
---
# Service with weighted routing (Canary)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
      # Gradually shift traffic to v1.3.0
      annotations:
        nginx.ingress.kubernetes.io/canary: "true"
        nginx.ingress.kubernetes.io/canary-weight: "20"
```

**Commands**:
```bash
# Apply blue-green deployment
kubectl apply -f deployment-blue-green.yaml

# Verify replicas and traffic routing
kubectl get pods -l version=v1.3.0
kubectl get svc app-service
```

---

### **2. Automated Rollback on Failure (Istio Canary)**
**Scenario**: Roll back to `v1.2.0` if the new version (`v1.3.0`) has a >5% error rate.

```yaml
# canary-analysis.yaml (Istio)
apiVersion: networking.istio.io/v1alpha3
kind: Canary
metadata:
  name: app-canary
spec:
  trafficRouting:
    latestRevision: web-v1.3.0  # New version
    stableRevision: web-v1.2.0  # Fallback
  analysis:
    metrics:
    - name: request_count
      threshold: 2000  # Min requests for analysis
    - name: error_percentage
      threshold: 5    # Roll back if >5% errors
    interval: 1m
```

**Commands**:
```bash
# Install Istio and apply Canary
kubectl apply -f istio.yaml
kubectl apply -f canary-analysis.yaml

# Monitor rollout
kubectl get canary
```

---

### **3. Terraform for Immutable EC2 Instances**
**Scenario**: Launch a new EC2 instance from a **golden AMI** (pre-configured, immutable).

```hcl
# main.tf
resource "aws_instance" "app_server" {
  ami                    = "ami-0c55b159cbfafe1f0"  # Golden AMI (pre-validated)
  instance_type          = "t3.medium"
  subnet_id              = aws_subnet.public.id
  iam_instance_profile   = aws_iam_instance_profile.app.name
  user_data              = filebase64("user-data.sh")  # Minimal config (no manual edits)
  tags = {
    Name    = "app-server-v1.2.0"
    Version = "v1.2.0"
  }
  lifecycle {
    prevent_destroy = true  # Never modify; replace instead
    ignore_changes   = [tags]  # Tags only for labels
  }
}

# User data (runs once at launch)
# user-data.sh
#!/bin/bash
echo "Running pre-validated config" > /etc/version
systemctl restart app
```

**Commands**:
```bash
# Plan and apply
terraform plan
terraform apply

# Replace old instance (e.g., after patching the golden AMI)
terraform apply -target=aws_instance.app_server
```

---

### **4. AWS CodeDeploy for Immutable Lambda Functions**
**Scenario**: Deploy a new Lambda version (`v1.3.0`) with automatic rollback.

```yaml
# codedeploy-appspec.yml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::CodeDeploy::Application
      Name: my-lambda-app
    DeploymentGroup:
      Type: AWS::CodeDeploy::DeploymentGroup
      ApplicationName: my-lambda-app
      DeploymentConfigName: CodeDeployDefault.Lambda Canary10Percent5Minutes
      ServiceRoleArn: arn:aws:iam::123456789012:role/aws-codedeploy-lambda-role
      Deployment:
        ApplicationStopTraffic: true
        DeploymentStopTraffic: true
```

**Commands**:
```bash
# Package and deploy
aws lambda publish-version --function-name my-function --image-uri registry.example.com/my-function:v1.3.0
aws codedeploy create-deployment --application-name my-lambda-app --deployment-group-name my-lambda-group
```

---

## **Validation Checks**
| **Check**                          | **Tool/Method**                          | **Purpose**                                                                 |
|-------------------------------------|-------------------------------------------|----------------------------------------------------------------------------|
| Container Integrity                 | `docker scan`, Trivy                   | Scan for vulnerabilities in images.                                        |
| Health Probe                        | Kubernetes `livenessProbe`               | Ensure instance is operational before traffic.                             |
| Configuration Drift                 | `kubectl diff` + Git History            | Compare live configs to desired state.                                    |
| Rollback Success                    | CI/CD Pipeline Logs                      | Verify rollback completed without failures.                                |
| Traffic Shift Metrics                | Prometheus + Grafana                    | Monitor error rates, latency post-deployment.                             |

---

## **Related Patterns**
| **Pattern**                          | **Relationship to Immutable Infrastructure**                                                                 | **When to Use**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Infrastructure as Code (IaC)**      | Enables reproducible, version-controlled infrastructure.                                               | Always pair with immutable infra to avoid manual drift.                        |
| **Canary Deployments**                | Gradually shifts traffic to new versions, reducing risk.                                              | Best for stateful services or high-traffic apps.                              |
| **Feature Flags**                    | Dynamically enable/disable features in releases.                                                       | Use with canary deployments for A/B testing.                                 |
| **Serverless (AWS Lambda, Knative)**  | Functions are ephemeral and immutable by design.                                                     | Ideal for event-driven, stateless workloads.                                  |
| **Blue-Green Deployments**            | Instant switch between environments; zero downtime.                                                   | Suitable for low-latency services (e.g., APIs).                              |
| **GitOps (ArgoCD, Flux)**             | Syncs Kubernetes manifests from Git, enforcing immutability.                                         | Perfect for Kubernetes-native immutable deployments.                         |
| **Configuration as Code**            | Externalizes all configs (e.g., Kubernetes ConfigMaps).                                             | Required for stateless designs.                                               |
| **Chaos Engineering**                 | Tests resilience by injecting failures (e.g., pod kills).                                             | Validate rollback and self-healing mechanisms.                                 |

---

## **Best Practices**
1. **Minimize Image Layers**:
   - Use multi-stage Dockerfiles to reduce attack surface.
   - Example:
     ```dockerfile
     # Build stage
     FROM golang:1.19 as builder
     WORKDIR /app
     COPY . .
     RUN go build -o /app/bin/app

     # Runtime stage
     FROM alpine:latest
     COPY --from=builder /app/bin/app /app/
     CMD ["/app/app"]
     ```

2. **Enforce Versioning**:
   - Tag all images/containers with semantic versioning (e.g., `app:v1.2.3`).
   - Use immutable tags (never `latest`).

3. **Automate Rollbacks**:
   - Configure CI/CD to auto-revert if health checks fail.
   - Example (GitHub Actions):
     ```yaml
     - name: Rollback on failure
       if: failure()
       run: |
         kubectl rollout undo deployment/app --to-revision=2
     ```

4. **Limit Admin Access**:
   - Restrict permissions to modify running instances (e.g., IAM policies with `onlyAllow` for deployments).

5. **Monitor Drift**:
   - Use tools like **Kubectl Diff** or **Terraform Plan** to detect unintended changes.

6. **Document Recovery Procedures**:
   - Outline steps to restore from backups (e.g., RDS snapshots, EBS volumes).

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**                     | **Risk**                                                                 | **Fix**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **Manual Patching**                   | Introduces drift and inconsistencies.                                    | Use pre-built images/AMIs.                                             |
| **Persistent Local Configs**          | Configs change between deployments.                                       | Store configs in Secrets/ConfigMaps.                                  |
| **Long-Lived Instances**              | Harder to replace; accumulates tech debt.                                | Set TTL or use session-based scaling.                                  |
| **No Rollback Plan**                  | Failed deployments cause outages.                                         | Implement automated rollbacks or blue-green.                          |
| **Ignoring Image Vulnerabilities**    | Exploitable containers in production.                                    | Scan images pre-deployment (e.g., Trivy).                             |

---
**Key Takeaway**: Immutable Infrastructure reduces complexity by eliminating the need to update running systems. Focus on **automation, validation, and statelessness** to ensure resilience and consistency. For further reading, explore [Google’s Site Reliability Engineering (SRE) principles](https://sre.google/sre-book/table-of-contents/) or [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/).