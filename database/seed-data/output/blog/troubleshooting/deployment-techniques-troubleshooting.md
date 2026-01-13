# **Debugging Deployment Techniques: A Troubleshooting Guide**

Deploying applications reliably is critical for system stability and user experience. Misconfigurations, network issues, or incomplete rollouts can lead to downtime, degraded performance, or data corruption. This guide covers **common deployment pitfalls**, **diagnostic steps**, **fixes**, and **prevention strategies** to ensure smooth deployments.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue with these symptoms:

| **Symptom**                     | **Description**                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|
| **Failed rollout**              | Deployment stalls, hangs, or rolls back automatically.                         |
| **Partial deployment**          | Some services/containers fail to start, while others succeed.                   |
| **High latency/timeout errors** | Services respond slowly or time out after deployment.                          |
| **Data inconsistency**          | Database corruption, missing records, or stale reads post-deployment.          |
| **Resource exhaustion**         | CPU/memory/bandwidth spikes after deployment.                                   |
| **Misconfigured parameters**    | Environment variables, secrets, or configs not applied correctly.              |
| **Rollback initiated**          | System reverts to a previous version due to health checks or manual intervention. |
| **API/endpoint failures**       | Services return 5xx errors or incorrect responses post-deployment.              |
| **Log spam/errors**             | Unusual error logs in application, container, or orchestration logs.           |

---
## **2. Common Issues & Fixes**

### **2.1 Deployment Stalls or Hangs**
**Cause:**
- **Orchestration issue** (Kubernetes stuck in `Pending`/`CrashLoopBackOff`).
- **Resource contention** (CPU/memory limits hit during startup).
- **Slow dependency resolution** (Docker images not pulled in time).
- **Network policies blocking traffic**.

**Debugging Steps:**
1. **Check pod/container status:**
   ```sh
   kubectl get pods -n <namespace> --watch
   ```
   - If stuck in `Pending`, inspect:
     ```sh
     kubectl describe pod <pod-name> -n <namespace>
     ```
     Look for `Events` related to `FailedScheduling`, `CrashLoopBackOff`, or `ImagePullBackOff`.

2. **Verify resource limits:**
   ```yaml
   # Example: Increment CPU/memory limits in Deployment manifest
   resources:
     limits:
       cpu: "1"
       memory: "512Mi"
     requests:
       cpu: "500m"
       memory: "256Mi"
   ```

3. **Increase startup timeout (Kubernetes):**
   ```yaml
   spec:
     terminationGracePeriodSeconds: 30  # Extend shutdown time
     containers:
     - readinessProbe:
         initialDelaySeconds: 5
         periodSeconds: 10
   ```

4. **Check network policies:**
   ```sh
   kubectl get networkpolicies -A
   ```
   Ensure no policy blocks inter-pod traffic.

**Fix:**
- **Scale up clusters temporarily** during deployments.
- **Pre-pull images** to avoid `ImagePullBackOff`:
  ```sh
  kubectl rollout restart deployment/<deployment-name>
  ```

---

### **2.2 Partial Deployment (Some Services Fail)**
**Cause:**
- **Misconfigured `initContainers`** (dependencies not ready).
- **Health checks failing** (`livenessProbe` or `readinessProbe` too strict).
- **Dependency version mismatch** (e.g., DB schema too new for the app).
- **Sidecar containers crashing** (e.g., log shippers, monitors).

**Debugging Steps:**
1. **Inspect failing pods:**
   ```sh
   kubectl logs <failing-pod> -n <namespace> --previous  # Check prior logs
   ```
   - Look for connection errors, timeouts, or `5xx` responses.

2. **Check health probes:**
   ```yaml
   # Example: Adjust probe thresholds in Deployment
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
     initialDelaySeconds: 10
     periodSeconds: 5
     failureThreshold: 3
   ```

3. **Verify init containers:**
   ```yaml
   initContainers:
   - name: wait-for-db
     image: busybox
     command: ['sh', '-c', 'until nslookup db-service; do echo waiting for DB; sleep 2; done;']
   ```

**Fix:**
- **Slow-start dependencies** (e.g., DB):
  ```sh
  kubectl annotate deployment/<deployment> kubectl.kubernetes.io/default-container=app
  ```
  Then scale up manually to verify.
- **Retry failed probes** with exponential backoff.

---

### **2.3 High Latency/Timeout Errors Post-Deployment**
**Cause:**
- **Increased load** (traffic spike after rollout).
- **Slow cold starts** (serverless functions, containers).
- **Database bottlenecks** (unoptimized queries).
- **Network latency** (CDN misconfiguration, DNS issues).

**Debugging Steps:**
1. **Monitor latency metrics:**
   ```sh
   kubectl top pods -n <namespace>  # Check CPU/memory usage
   ```
   - Use Prometheus/Grafana for deeper insights:
     ```sh
     curl http://<prometheus-server>:9090/api/v1/query?query=rate(http_request_duration_seconds_bucket{job="your-app"}[1m])
     ```

2. **Check DB queries:**
   - Enable slow query logs in PostgreSQL/MySQL:
     ```sql
     -- MySQL example
     SET GLOBAL slow_query_log = 'ON';
     SET GLOBAL long_query_time = 1;
     ```
   - Review `pg_stat_statements` (PostgreSQL).

3. **Test network paths:**
   ```sh
   traceroute <service-endpoint>
   mtr --report <service-endpoint>
   ```

**Fix:**
- **Optimize queries** (add indexes, denormalize data).
- **Implement caching** (Redis, CDN).
- **Scale horizontally** if load is the issue:
  ```sh
  kubectl scale deployment/<deployment> --replicas=5
  ```

---

### **2.4 Data Inconsistency After Deployment**
**Cause:**
- **Incomplete migrations** (schema changes not applied).
- **Transaction rollbacks** (DB retry logic).
- **Race conditions** (e.g., WebSocket connections lost during restart).
- **Backup corruption** (pre-deployment snapshots failed).

**Debugging Steps:**
1. **Verify migrations:**
   - Check DB logs for `ALTER TABLE` success/failure:
     ```sh
     grep "ALTER TABLE" /var/log/postgresql/postgresql-.log
     ```
   - Run migrations manually:
     ```sh
     rails db:migrate  # Rails
     flask db upgrade  # Flask-Migrate
     ```

2. **Inspect transactions:**
   - Check `pg_stat_activity` (PostgreSQL):
     ```sql
     SELECT * FROM pg_stat_activity WHERE state = 'active';
     ```
   - Look for long-running transactions.

3. **Audit change logs:**
   ```sh
   kubectl exec <pod> -- bash -c "journalctl -u your-app --no-pager | grep -i 'error'"
   ```

**Fix:**
- **Roll back migrations** if partial:
  ```sh
  rails db:rollback STEP=1  # Rollback last migration
  ```
- **Use compensating transactions** for critical operations.
- **Test in staging** with production-like data before rolling out.

---

### **2.5 Resource Exhaustion (CPU/Memory/Bandwidth)**
**Cause:**
- **Memory leaks** (unreleased objects in app code).
- **Disk I/O saturation** (log files not rotated).
- **Network saturation** (unlimited retries in clients).
- **Improper autoscaling** (no CPU-based scaling).

**Debugging Steps:**
1. **Check resource limits:**
   ```sh
   kubectl top nodes
   kubectl describe node <node-name>
   ```
   - Look for `MemoryPressure` or `DiskPressure`.

2. **Profile memory usage:**
   - Use `pprof` (Go):
     ```sh
     go tool pprof http://<pod-ip>:<port>/debug/pprof/heap
     ```
   - Or `heaptrack` (C++).

3. **Monitor network bandwidth:**
   ```sh
   kubectl top pods --containers=true -n <namespace>
   ```

**Fix:**
- **Set resource requests/limits** strictly:
  ```yaml
  resources:
    requests:
      cpu: "200m"
      memory: "256Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
  ```
- **Enable horizontal pod autoscaling (HPA):**
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: <deployment>
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: <deployment>
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
- **Rotate logs** (e.g., `logrotate` for `syslog`).

---

### **2.6 Misconfigured Parameters/Secrets**
**Cause:**
- **Hardcoded secrets** (not using `Secrets` or `ConfigMaps`).
- **Environment variable leaks** (visible in pod logs).
- **Incorrect file permissions** (secrets exposed via `/etc/secrets`).
- **Version skew** (secrets not updated in all environments).

**Debugging Steps:**
1. **Audit environment variables:**
   ```sh
   kubectl exec <pod> -- printenv
   ```
   - Check for plaintext secrets.

2. **Verify Secrets/ConfigMaps:**
   ```sh
   kubectl get secrets -n <namespace>
   kubectl describe secret <secret-name> -n <namespace>
   ```

3. **Check mount points:**
   ```sh
   kubectl exec <pod> -- ls /etc/secrets
   ```

**Fix:**
- **Use Kubernetes Secrets** (base64-encoded):
  ```yaml
  volumes:
  - name: secrets-volume
    secret:
      secretName: my-secrets
  ```
- **Rotate secrets** post-deployment:
  ```sh
  kubectl delete secret my-secrets -n <namespace>
  kubectl create secret generic my-secrets --from-literal=DB_PASSWORD=new_password -n <namespace>
  ```
- **Use tools like Vault or HashiCorp Nomad** for dynamic secrets.

---

### **2.7 Automatic Rollback Triggered**
**Cause:**
- **Liveness probe failures** (app crashes on startup).
- **Readiness probe failures** (app not ready for traffic).
- **Resource constraints** (OOM kills pods).
- **Custom rollback logic** (e.g., CI/CD pipeline failure).

**Debugging Steps:**
1. **Check rollout history:**
   ```sh
   kubectl rollout history deployment/<deployment> -n <namespace>
   ```

2. **Inspect failed pods:**
   ```sh
   kubectl get events --sort-by=.metadata.creationTimestamp -n <namespace>
   ```

3. **Replicate locally:**
   ```sh
   kubectl port-forward svc/<service> 8080:80
   curl http://localhost:8080/health  # Test manually
   ```

**Fix:**
- **Adjust probe thresholds** (as shown earlier).
- **Exclude unstable pods from service discovery** (use `externalTrafficPolicy: Local` in Service):
  ```yaml
  spec:
    externalTrafficPolicy: Local
    selector:
      app: my-app
  ```
- **Debug locally** before rolling out.

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                                                                 | **Command/Example**                          |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **kubectl debug**        | Debug failed containers interactively.                                     | `kubectl debug -it <pod> --image=busybox`   |
| **Port forwarding**      | Test endpoints locally.                                                     | `kubectl port-forward svc/<service> 8080:80` |
| **Prometheus + Grafana** | Monitor metrics (latency, errors, saturation).                             | `http://<prometheus>:9090/targets`          |
| **Log aggregation**      | Centralize logs (Fluentd, Loki, ELK).                                       | `kubectl logs -f <pod> --tail=50`           |
| **Distributed tracing**  | Trace requests across services (Jaeger, Zipkin).                            | `curl http://<jaeger-query>:16686`          |
| **Chaos Engineering**    | Test resilience (Chaos Mesh, Gremlin).                                     | `kubectl apply -f chaos-mesh.yaml`          |
| **Database auditing**    | Track schema changes (pgAudit, MySQL Audit Plugin).                          | `SELECT * FROM pg_stat_activity;`            |
| **Syntax checking**      | Validate YAML/manifests before applying.                                    | `kubectl apply --dry-run=client -f manifest.yaml` |

---

## **4. Prevention Strategies**

### **4.1 Pre-Deployment Checks**
- **Unit/Integration Tests:**
  ```sh
  make test  # Run tests in CI
  ```
- **Canary Releases:**
  - Deploy to a small subset of users first.
  - Use **Flagger** for automated canary analysis:
    ```yaml
    apiVersion: flagger.app/v1beta1
    kind: Canary
    metadata:
      name: my-app
    spec:
      targetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: my-app
      service:
        port: 9898
      analysis:
        interval: 1m
        threshold: 5
        maxWeight: 50
        stepWeight: 10
    ```

- **Database Schema Validation:**
  - Use **Flyway** or **Liquibase** for migrations:
    ```xml
    <!-- Example Flyway config -->
    <databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
            https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.2.xsd">
        <changeSet id="1" author="me">
            <createTable tableName="users">
                <column name="id" type="int" autoIncrement="true"/>
                <column name="name" type="varchar(255)"/>
            </createTable>
        </changeSet>
    </databaseChangeLog>
    ```

### **4.2 Post-Deployment Monitoring**
- **Alerting Rules:**
  - Set up alerts for:
    - `ErrorBudgetBurnRate` (SLO violations).
    - `PodRestartCount` (crashing pods).
    - `DiskPressure` or `MemoryPressure`.
  - Example Prometheus alert:
    ```yaml
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate on {{ $labels.instance }}"
    ```
- **Automated Rollback Triggers:**
  - Roll back if:
    - Error rate > 5% for 5 minutes.
    - Latency P99 > 1s for 5 minutes.
  - Configure in **Flagger** or **Argo Rollouts**:
    ```yaml
    progressDeadlineSeconds: 600  # Wait 10 mins for canary to stabilize
    ```

### **4.3 Infrastructure as Code (IaC)**
- **Template Validation:**
  - Use **kubeval** to validate manifests:
    ```sh
    kubeval -d ./manifests/
    ```
- **GitOps Workflows:**
  - Use **ArgoCD** or **Flux** for declarative deployments.
- **Backup Strategies:**
  - Schedule **Velero backups**:
    ```sh
    velero backup create daily-backup --include-namespaces=production
    ```

### **4.4 Security Hardening**
- **Pod Security Policies (PSP) / OPA Gatekeeper:**
  ```yaml
  # Example: Restrict privileged containers
  apiVersion: policy/v1beta1
  kind: PodSecurityPolicy
  metadata:
    name: restricted
  spec:
    privileged: false
    allowPrivilegeEscalation: false
    requiredDropCapabilities:
      - ALL
    volumes:
      - 'configMap'
      - 'secret'
  ```
- **Network Policies:**
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: deny-all-except-frontend
  spec:
    podSelector: {}
    policyTypes:
    - Ingress
    ingress:
    - from:
      - podSelector:
          matchLabels:
            app: frontend
  ```

### **4.5 Documentation & Runbooks**
- **Deployment Checklist:**
  ```markdown
  ## Pre-Deployment Checklist
  - [ ] Run `kubectl apply --dry-run=client -f manifest.yaml`
  - [ ] Verify `kubectl get pods -w` shows no errors
  - [ ] Check `kubectl logs <pod>` for startup issues
  - [ ] Test endpoints: `curl http://<service>:<port>/health`
  ```
- **Incident Response Plan:**
  - **Step 1:** Identify affected services.
  - **Step 2:** Roll back if critical (use `kubectl rollout undo`).
  - **Step 3:** Open a postmortem with:
    - Root cause analysis.
    - Immediate fixes.
    - Long-term prevention.

---

## **5. Summary of Key Takeaways**
| **Issue**               | **Quick Fix**                          | **Long-Term Solution**                     |
|-------------------------|----------------------------------------|--------------------------------------------|
| Deployment stalls       | Increase resource limits