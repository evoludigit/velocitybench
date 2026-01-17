---
# **[Pattern] Rolling Deployments & Zero-Downtime Updates – Reference Guide**

---

## **1. Overview**
Rolling Deployments ensure **high availability** by gradually replacing old application instances with new ones during updates, minimizing service interruptions. This pattern is critical for **stateless applications** (or those with persistency managed externally, like databases) and supports **microservices architectures**. By deploying updates to a subset of instances at a time—while maintaining the total number of running instances—users experience **near-zero downtime**, transparent failovers, and resilient traffic routing.

Key Benefits:
- **No service disruption** (users remain unaffected).
- **Graceful rollback** (quick rollback if issues arise).
- **Traffic-based failover** (healthy instances handle requests).
- **Scalability** (works across single nodes, clusters, or cloud deployments).

Applicable Use Cases:
- Web applications (e.g., e-commerce platforms).
- APIs and microservices.
- Distributed systems (Kubernetes, Docker Swarm, AWS ECS).
- Automated CI/CD pipelines.

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                                     |
|------------------------|--------------------------------------------------------------------------------------------------|
| **Rolling Update**     | Gradual replacement of instances (e.g., 10% per minute).                                          |
| **Replica Set**        | Pool of identical instances providing redundancy.                                                  |
| **Health Check**       | Mechanism to verify if instances are responding (e.g., `/health` endpoint).                     |
| **Traffic Routing**    | Load balancers (e.g., Nginx, AWS ALB) distribute requests to healthy instances.                   |
| **Blue-Green**         | Alternative to rolling updates (full swap of environments).                                        |
| **Canary Release**     | Partial rollout to a small user segment before full deployment.                                     |
| **Rollback Window**    | Timeframe to revert changes if stability is compromised (e.g., 5 minutes).                       |

---

## **3. Schema Reference**
### **3.1 Core Components**
| **Component**       | **Purpose**                                                                                     | **Example Tools/Technologies**                     |
|---------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Orchestrator**    | Manages instance lifecycle (scaling, updates).                                                  | Kubernetes, Docker Swarm, Nomad                     |
| **Load Balancer**   | Routes traffic to healthy instances; detects failed pods.                                       | Nginx, HAProxy, AWS ALB, Traefik                   |
| **Update Strategy** | Defines how instances are replaced (e.g., sequential, parallel).                               | Kubernetes `RollingUpdate` policy                  |
| **Health Probe**    | Validates instance readiness; triggers replacements if unhealthy.                               | LivenessProbe, ReadinessProbe (K8s)                |
| **Configuration**   | Externalized settings (e.g., env vars, config maps) to avoid code redeployment.                | Consul, etcd, Kubernetes ConfigMaps                |
| **CI/CD Pipeline**  | Automates builds, tests, and rolling deployments.                                               | Jenkins, GitHub Actions, ArgoCD, Spinnaker          |
| **Monitoring**      | Tracks performance/metrics (e.g., latency, error rates).                                       | Prometheus, Datadog, New Relic                      |

---

### **3.2 Deployment Phases**
| **Phase**           | **Action**                                                                                     | **Key Metrics**                              |
|---------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Pre-Rollout**     | Backup critical data; validate rollout plan (e.g., traffic splits).                          | Deployment approval rate, user segment size  |
| **Rolling Out**     | Replace instances one-by-one (e.g., 10% every 30s).                                           | Instance readiness %, error rates            |
| **Post-Rollout**    | Monitor for regressions; verify full coverage.                                                 | System uptime, latency percentiles           |
| **Rollback**        | Revert to previous version if issues detected (e.g., 50% traffic shift back).                 | Time to detect failure, recovery time         |

---

## **4. Implementation Steps**
### **4.1 Prerequisites**
- Stateless application (or external database).
- Load balancer (e.g., Kubernetes `Service`, AWS ALB).
- Health checks (e.g., HTTP endpoints).
- CI/CD pipeline with automation (e.g., GitHub Actions).

### **4.2 Step-by-Step Workflow**
1. **Define Rollout Strategy**:
   - Set `maxSurge` (extra instances allowed during update) and `maxUnavailable` (max instances that can be down).
     ```yaml
     # Kubernetes Deployment Example
     strategy:
       type: RollingUpdate
       rollingUpdate:
         maxSurge: 25%
         maxUnavailable: 15%
     ```

2. **Deploy New Version**:
   - Update container image (e.g., via `kubectl set image`).
   - Orchestrator replaces instances sequentially (e.g., 1 pod → 1 new pod → 2 old + 2 new).

3. **Validate Health**:
   - Load balancer checks health probes (e.g., `/health` returns `200`).
   - Skip unhealthy instances; fail traffic to others.

4. **Monitor & Rollback (if needed)**:
   - Use alerts (e.g., Prometheus + Alertmanager) for errors.
   - Trigger rollback if error rate > threshold (e.g., 1%).
     ```sh
     # Example: Kubernetes rollback
     kubectl rollout undo deployment/my-app
     ```

5. **Post-Rollout Verification**:
   - Run smoke tests (e.g., API endpoints).
   - Compare metrics (e.g., latency, throughput) pre/post-update.

---

## **5. Query Examples**
### **5.1 Kubernetes Commands**
| **Command**                          | **Purpose**                                  |
|--------------------------------------|---------------------------------------------|
| `kubectl rollout status deployment/my-app` | Check rollout progress.                     |
| `kubectl get pods -o wide`             | List pods with node assignments.            |
| `kubectl describe deployment/my-app`   | View update strategy details.               |
| `kubectl logs <pod-name>`             | Debug instance logs.                        |

### **5.2 CI/CD Pipeline Snippets**
```yaml
# GitHub Actions Workflow (Rolling Deployment)
name: Rolling Deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & Push Image
        run: |
          docker build -t my-app:${{ github.sha }} .
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push my-app:${{ github.sha }}
      - name: Deploy to Kubernetes
        uses: azure/k8s-set-context@v3
        with:
          method: kubeconfig
        env:
          GITHUB_SHA: ${{ github.sha }}
        run: |
          kubectl set image deployment/my-app my-app=my-app:${{ env.GITHUB_SHA }}
          kubectl rollout status deployment/my-app --timeout=5m
```

---

## **6. Troubleshooting**
| **Issue**                          | **Diagnosis**                                  | **Solution**                                  |
|-------------------------------------|------------------------------------------------|-----------------------------------------------|
| **Traffic stuck on old instances** | Health probe failing or load balancer misconfig. | Check `kubectl describe service`; verify probes. |
| **Slow rollout**                    | High `maxSurge` or slow pod startup.           | Reduce `maxSurge`; optimize image layers.     |
| **Rollback failed**                 | New version incompatible with old config.       | Manually revert in orchestration system.      |
| **Database inconsistencies**        | Stateful app assuming local storage.           | Use external DB (e.g., PostgreSQL Replica).   |

---

## **7. Related Patterns**
| **Pattern**                  | **Purpose**                                                                 | **When to Use**                                  |
|------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Blue-Green Deployment**    | Full swap of environments (zero downtime but higher resource cost).        | Critical updates where incremental risk is high.  |
| **Canary Releases**          | Gradual rollout to a small user segment.                                    | Feature flags or high-risk changes.              |
| **Feature Flags**            | Toggle features dynamically without redeployment.                          | A/B testing or gradual rollouts.                 |
| **Circuit Breaker**          | Prevent cascading failures by isolating faulty services.                    | Microservices with external dependencies.       |
| **Database Replication**     | Maintain data consistency across instances.                                | Stateful applications.                          |

---

## **8. Best Practices**
- **Test Rollback**: Simulate failures in staging to validate rollback speed.
- **Traffic Shifts**: Use tools like Istio or Linkerd for fine-grained traffic control.
- **Logging/Metrics**: Correlate logs (e.g., ELK Stack) with metrics (e.g., Prometheus).
- **Auto-Scaling**: Pair with horizontal pod autoscaler (HPA) to handle traffic spikes.
- **Document Rollout Plan**: Define SLOs (e.g., "99.9% uptime"), rollback criteria, and owners.

---
**References**:
- [Kubernetes Rolling Updates Docs](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)
- [AWS Blue/Green Deployments](https://aws.amazon.com/elasticbeanstalk/features/blue-green-deployments/)
- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)