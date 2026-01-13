# **[Pattern] Deployment Approaches Reference Guide**

---

## **Overview**
This reference guide outlines the **Deployment Approaches** pattern, a structured methodology for deploying applications, services, or infrastructure in various environments (e.g., on-premises, cloud, hybrid). The pattern categorizes deployment strategies based on complexity, automation, and resource management needs—enabling teams to select the right approach for **reliability, scalability, cost-efficiency, and compliance**.

Key considerations include:
- **Deployment speed** (manual vs. automated)
- **Downtime tolerance** (rolling, blue-green, canary)
- **Scalability** (elastic vs. fixed resource allocation)
- **Rollback mechanisms** (revert to prior version, graceful degradation)

Best suited for: DevOps engineers, cloud architects, and site reliability engineers (SREs) evaluating deployment trade-offs.

---

## **Schema Reference**
| **Category**          | **Subcategory**               | **Description**                                                                                     | **Use Case Examples**                                                                                     |
|-----------------------|--------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Deployment Type**   | **Monolithic**                | Single, bundled deployment of application + dependencies.                                           | Legacy applications, simple microservices bundles.                                                  |
|                       | **Modular (Microservices)**    | Independent deployments per service/component (e.g., Kubernetes pods).                             | Cloud-native apps, polyglot architectures.                                                            |
|                       | **Serverless**                | Event-triggered functions (e.g., AWS Lambda) with no managed infrastructure.                       | Spiky workloads (e.g., APIs, data processing).                                                      |
|                       | **Containerized**             | Deployments packaged in containers (Docker) and orchestrated (e.g., Kubernetes, Docker Swarm).       | Kubernetes clusters, Kubernetes Engine (GKE), Azure Kubernetes Service (AKS).                         |
| **Rollout Strategy**  | **Big Bang**                  | Full deployment at once (high risk; minimal downtime monitoring).                                   | Internal tooling, feature flags for safety.                                                          |
|                       | **Rolling Update**            | Gradually replaces instances (e.g., 10% at a time).                                                 | Web apps, API services (controlled risk).                                                             |
|                       | **Blue-Green**                | Two identical environments: traffic shifts from "blue" to "green."                                  | High-traffic SaaS apps (e.g., Netflix, Uber).                                                      |
|                       | **Canary**                    | Deploys to a subset of users (e.g., 5% traffic).                                                  | A/B testing, gradual feature rollouts.                                                              |
|                       | **Dark Launch**               | Deployment without user exposure (enables testing post-launch).                                     | Secret experiments, compliance checks.                                                               |
| **Infrastructure**   | **On-Premises**               | Deployments on local servers (e.g., VMs, bare metal).                                                | Legacy systems, compliance-sensitive workloads.                                                      |
|                       | **Public Cloud**              | Managed services (e.g., AWS EC2, GCP Compute Engine).                                                | Scalable, pay-as-you-go deployments (e.g., startups, global apps).                                      |
|                       | **Hybrid**                    | Combination of on-premises + cloud (e.g., Kubernetes on AWS Outposts).                             | Regulatory requirements + cloud scalability (e.g., banking, healthcare).                             |
|                       | **Multi-Cloud**               | Deployments across multiple clouds (e.g., Azure + AWS).                                             | Vendor lock-in avoidance, redundancy.                                                               |
| **Orchestration**     | **Manual**                    | Human-led deployments (e.g., SSH, Git commit triggers).                                             | Small teams, infrequent updates.                                                                       |
|                       | **CI/CD Pipeline**            | Automated deployments via tools (e.g., Jenkins, GitHub Actions, ArgoCD).                           | Agile teams, continuous delivery.                                                                     |
|                       | **GitOps**                    | Declarative infrastructure-as-code (e.g., Git + Kubernetes manifests).                             | Kubernetes, ArgoCD/Flux for declarative sync.                                                        |
| **Scaling**           | **Vertical Scaling**          | Increasing resource allocation (CPU/RAM) for a single instance.                                     | Monolithic apps with predictable workloads.                                                         |
|                       | **Horizontal Scaling**        | Adding more instances (e.g., auto-scaling groups).                                                  | Stateless apps, microservices.                                                                      |
|                       | **Serverless Auto-Scaling**   | Dynamically scales functions (e.g., AWS Lambda concurrent executions).                              | Event-driven workloads (e.g., file processing, APIs).                                               |
| **Rollback Strategy** | **Instant Revert**            | Immediate rollback to previous version (e.g., Kubernetes `rollback`).                              | Critical failures (e.g., API crashes).                                                               |
|                       | **Feature Toggle**            | Conditionally enable/disable features via code flags.                                                 | Progressive rollouts, bug fixes.                                                                     |

---

## **Implementation Details**
### **1. Selecting a Deployment Approach**
- **Startups/MVPs:** Use **serverless** (cost-effective) or **containerized** (scalability) with **CI/CD** pipelines.
- **Enterprise:** Prefer **hybrid/multi-cloud** with **GitOps** for compliance and **blue-green** for zero-downtime updates.
- **High Traffic:** **Canary + auto-scaling** (e.g., Kubernetes HPA) to mitigate risks.

### **2. Automation & Tooling**
| **Tool**               | **Purpose**                                                                 | **Example Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Kubernetes**         | Orchestrates containerized workloads (scaling, rolling updates).            | Deploying a React frontend with 100+ pods.                                            |
| **Terraform**          | Infrastructure-as-code (IaC) for cloud resources.                            | Provisioning AWS EKS clusters.                                                        |
| **ArgoCD/Flux**        | GitOps for Kubernetes: syncs manifests from Git.                           | Syncing microservices with canary deployments.                                        |
| **Jenkins/GitHub Actions** | CI/CD pipelines for automated builds/deployments.                        | Testing + deploying a Python API on AWS ECS.                                           |
| **Ansible**            | Configuration management for on-premises servers.                          | Updating 50 VMs with a new security patch.                                            |
| **AWS CodeDeploy**     | Managed rolling updates for Lambda/containers.                            | Deploying a Node.js app to AWS Fargate.                                                |

### **3. Key Configuration Examples**
#### **Kubernetes Rolling Update**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%  # Allow 25% extra pods during update
      maxUnavailable: 15%  # Tolerate 15% downtime
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.25.0  # New version
```
**Trigger:** `kubectl apply -f deployment.yaml`
**Rollback:** `kubectl rollout undo deployment/my-app`

#### **AWS Blue-Green Deployment (Lambda)**
1. **Deploy "Green" version** (e.g., `my-api-v2`) alongside "Blue" (active).
2. **Update alias** in AWS Lambda:
   ```bash
   aws lambda update-alias --function-name my-api \
     --name Production --function-version alias:my-api-v2
   ```
3. **Traffic shift:** 100% to `v2`; monitor for 1 hour before deleting `v1`.

#### **GitOps with ArgoCD**
1. **Store manifests in Git** (e.g., `manifests/prod/nginx-service.yaml`).
2. **Configure ArgoCD app sync:**
   ```yaml
   # argocd-app.yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: nginx-app
   spec:
     source:
       repoURL: https://github.com/myorg/manifests
       path: prod/nginx
       targetRevision: HEAD
     destination:
       server: https://kubernetes.default.svc
       namespace: default
     syncPolicy:
       automated:  # Auto-sync on Git changes
         prune: true
   ```
3. **Sync:** `argocd app sync nginx-app`

---

## **Query Examples**
### **1. How do I deploy a microservice with zero downtime?**
- Use **blue-green deployment** or **canary releases** (via Kubernetes `service` annotations or Argo Rollouts).
- Example:
  ```bash
  # Blue-Green with Kubernetes
  kubectl label pod my-pod app-version=v1  # Mark current pods as v1
  kubectl apply -f v2-deployment.yaml      # Deploy v2
  kubectl label pod my-pod app-version=v2  # Shift traffic
  ```

### **2. What’s the fastest way to rollback a serverless function?**
- Use **AWS Lambda aliases + versions**:
  1. Deploy `v2` with a new alias (e.g., `Production`).
  2. Monitor; if issues arise, revert the alias to point to `v1`:
     ```bash
     aws lambda update-alias --function-name my-function \
       --name Production --function-version v1
     ```

### **3. How to scale a containerized app during peak traffic?**
- Configure **horizontal pod autoscaling (HPA)** in Kubernetes:
  ```yaml
  # hpa.yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: my-app-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: my-app
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  ```
- Apply with:
  ```bash
  kubectl apply -f hpa.yaml
  ```

### **4. Can I automate deployments for on-premises servers?**
- Use **Ansible playbooks** or **Puppet/Chef** for configuration management.
  Example Ansible playbook (`deploy.yml`):
  ```yaml
  - name: Update web server
    hosts: webservers
    tasks:
      - name: Install Nginx
        ansible.builtin.apt:
          name: nginx
          state: latest
      - name: Deploy app
        ansible.builtin.copy:
          src: files/app.tar.gz
          dest: /var/www/html
        notify: restart nginx
  ```
  Run with:
  ```bash
  ansible-playbook -i inventory.ini deploy.yml
  ```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)]** | Provisions/manages infrastructure via code (e.g., Terraform, CloudFormation).                     | Cloud deployments, reproducible environments.                                                      |
| **[GitOps]**                     | Synchronizes cluster state with Git repositories (e.g., ArgoCD, Flux).                               | Kubernetes environments, declarative workflows.                                                    |
| **[Canary Analysis]**             | Gradually exposes features to a subset of users for monitoring.                                      | High-traffic apps (e.g., Netflix, Stripe).                                                       |
| **[Chaos Engineering]**           | Proactively tests system resilience by injecting failures.                                         | Critical systems (e.g., e-commerce, healthcare).                                                 |
| **[Observability]**               | Monitors applications via metrics, logs, and traces (e.g., Prometheus, Jaeger).                    | Debugging deployments, SLA compliance.                                                              |
| **[Blue-Green Testing]**         | Validates new deployments in a staging environment before production.                              | High-risk updates (e.g., financial systems).                                                      |
| **[Progressive Delivery]**       | Combines canary + automated rollback for safe rollouts.                                            | Microservices, experiment-driven development.                                                      |

---

## **Best Practices**
1. **Start small:** Use **canary deployments** for new features before full rollouts.
2. **Automate rollbacks:** Configure CI/CD pipelines to revert on failure (e.g., Jenkins post-build hooks).
3. **Monitor aggressively:** Use **SLOs (Service Level Objectives)** to detect drift post-deployment.
4. **Document rollback steps:** Include recovery procedures in runbooks (e.g., "How to revert to v1.2.0").
5. **Leverage feature flags:** Enable gradual rollouts via tools like **LaunchDarkly** or **Unleash**.

---
**Notes:**
- For **stateful applications**, consider **volume snapshots** (e.g., Kubernetes `PersistentVolumeClaims`) during rolling updates.
- **Multi-region deployments** require **traffic routing** (e.g., AWS Global Accelerator) and **synchronous replication**.