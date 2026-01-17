# Debugging Rolling Deployments & Zero-Downtime Updates: A Troubleshooting Guide

## Version: 1.0
*Last Updated: [Insert Date]*
*Valid for: Kubernetes, Docker Swarm, Nomad, and other orchestration platforms*

---

## Introduction

Rolling deployments with zero-downtime updates are a cornerstone of modern DevOps practices, ensuring continuous availability while gradually testing new versions. This guide provides a practical, step-by-step approach to diagnosing and resolving common issues, with a focus on rapid resolution.

---

## Symptom Checklist

Before diving into debugging, verify these symptoms to isolate the problem:

1. **Service Unavailable Errors**
   - [ ] Error: `503 Service Unavailable` or `Connection Refused`
   - [ ] Partial outages (some users affected, not all)
   - [ ] Latency spikes or timeouts

2. **Rollback Failures**
   - [ ] Cannot rollback to previous version
   - [ ] Rollback triggers cascading failures
   - [ ] Health checks fail during rollback

3. **Database Issues**
   - [ ] Database migration fails during deployment
   - [ ] Validation errors during schema change
   - [ ] Connection pool exhaustion

4. **Startup/Health Check Problems**
   - [ ] Pods stuck in `CrashLoopBackOff` or `ContainerCreating`
   - [ ] Readiness probes fail
   - [ ] Liveness probes trigger restarts

5. **Traffic Distribution Issues**
   - [ ] Traffic not evenly distributed between versions
   - [ ] New version gets disproportionate load
   - [ ] Sticky sessions cause inconsistent behavior

6. **Metrics/Logging Anomalies**
   - [ ] Spikes in error rates or latency
   - [ ] Missing logs or incomplete traces
   - [ ] Metrics show uneven scaling

---

## Common Issues & Fixes

### 1. **Deployment Causes Outages (Symptoms: 503 errors, partial failures)**
#### Issue: **New version fails health checks, traffic directed to failing pods**
**Root Causes:**
- New code has breaking changes (e.g., missing environment variables).
- Database connection issues due to schema changes.
- External dependencies unreachable (e.g., Redis, APIs).

**Fixes:**

**A. Tighten Health Checks**
```yaml
# Example Kubernetes readiness probe (adjust thresholds)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
  timeoutSeconds: 5
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```
- **Action:** Add `/ready` endpoint to confirm all dependencies are up (e.g., DB, caches).
- **Pro tip:** Use `initialDelaySeconds` to avoid flapping during startup.

**B. Gradually Increase Traffic**
- **For Kubernetes:** Use `maxSurge` and `maxUnavailable` in deployments:
  ```yaml
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 15%
    type: RollingUpdate
  ```
- **For Istio/Linkerd:** Adjust traffic splitting (e.g., 90% old, 10% new).

**C. Debugging Steps:**
1. Check pod logs:
   ```sh
   kubectl logs <pod-name> -c <container> --previous  # For failed pods
   ```
2. Validate dependencies:
   ```sh
   # Test DB connection in the container
   kubectl exec -it <pod-name> -- curl -v http://db:5432
   ```
3. Verify environment variables:
   ```sh
   kubectl describe pod <pod-name> | grep Env
   ```

---

### 2. **Rollback Fails (Symptoms: Cannot revert, cascading failures)**
#### Issue: **Rollback stuck or introduces new bugs**
**Root Causes:**
- New version introduces critical bugs.
- Rollback strategy skips validation.
- Database state is inconsistent.

**Fixes:**

**A. Implement Canary Rollback**
- **Action:** Use a sidecar or init container to validate rollback health:
  ```dockerfile
  # Example: Init container to run smoke tests before rollback
  FROM alpine
  RUN apk add --no-cache curl
  CMD sh -c "curl -f http://localhost:8080/health || exit 1"
  ```
- **Kubernetes Example:**
  ```yaml
  initContainers:
  - name: health-check
    image: busybox
    command: ["sh", "-c", "until curl -f http://localhost:8080/health; do echo waiting; sleep 2; done"]
  ```

**B. Force Rollback with Validation**
- **Command (Kubernetes):**
  ```sh
  kubectl rollout undo deployment/<name> --to-revision=<N> --verify
  ```
- **Action:** Add `--verify` to ensure health checks pass.

**C. Database Rollback Plan**
- **For migrations:** Use transactional migrations (e.g., Flyway, Liquibase).
- **Action:** Implement a rollback migration script:
  ```sql
  -- Example: Downgrade a table
  CREATE TABLE users_old (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    -- ... old schema
  );
  INSERT INTO users_old SELECT * FROM users;
  DROP TABLE users;
  ALTER TABLE users_old RENAME TO users;
  ```

---

### 3. **Database Migrations Block Deployment**
#### Issue: **Deployment paused waiting for migrations**
**Root Causes:**
- Long-running migrations (e.g., ALTER TABLE).
- Migrations fail silently.
- No fallback to old schema.

**Fixes:**

**A. Parallelize Migrations**
- **Action:** Split large migrations into smaller batches:
  ```python
  # Example: Batch ALTER TABLE
  def migrate_in_batches(table, batch_size=1000):
      for offset in range(0, total_rows, batch_size):
          cursor.execute("ALTER TABLE %s ALTER COLUMN col DROP NOT NULL", (table,))
          cursor.execute(f"UPDATE %s SET col = NULL WHERE id > %d LIMIT %d",
                         (table, offset, batch_size))
  ```

**B. Use Backward-Compatible Migrations**
- **Strategy:** Add columns rather than altering them:
  ```sql
  -- Add new column instead of altering existing
  ALTER TABLE users ADD COLUMN bio TEXT;
  ```

**C. Timeout Migrations**
- **Kubernetes Example (Job for migrations):**
  ```yaml
  spec:
    activeDeadlineSeconds: 300  # Fail after 5 minutes
    template:
      spec:
        containers:
        - name: migrator
          image: my-migration-image
          command: ["/migrate.sh"]
  ```

---

### 4. **Startup Time Unpredictable (Symptoms: CrashLoopBackOff)**
#### Issue: **Pods take too long to start, causing traffic misrouting**
**Root Causes:**
- Slow dependency initialization (e.g., DB connections, caches).
- Large dependencies (e.g., ML models).
- Race conditions in startup logic.

**Fixes:**

**A. Pre-warm Dependencies**
- **Action:** Use init containers to bootstrap dependencies:
  ```yaml
  initContainers:
  - name: cache-warmup
    image: my-app
    command: ["sh", "-c", "until curl -s http://cache:6379/ping | grep PONG; do echo waiting; sleep 1; done"]
  ```

**B. Layered Startup Logic**
- **Code Example (Go):**
  ```go
  func main() {
      // Startup in phases
      if err := startDependencies(); err != nil {
          log.Fatalf("Failed to start dependencies: %v", err)
      }
      if err := initializeApp(); err != nil {
          log.Fatalf("Failed to initialize app: %v", err)
      }
      http.ListenAndServe(":8080", nil)
  }
  ```
- **Python Example:**
  ```python
  import threading

  def startup_phase(phase):
      print(f"Starting {phase}...")
      # Simulate work
      time.sleep(2)

  def main():
      threads = [
          threading.Thread(target=startup_phase, args=("DB",)),
          threading.Thread(target=startup_phase, args=("Cache",))
      ]
      for t in threads:
          t.start()
      threads[0].join()  # Wait for critical phase (DB)
      print("Ready!")
  ```

---

### 5. **Traffic Not Distributed Properly**
#### Issue: **Uneven traffic split (e.g., 100% new version)**
**Root Causes:**
- Misconfigured service mesh (Istio, Linkerd).
- Incorrect `maxSurge`/`maxUnavailable` settings.
- Sticky sessions overriding traffic split.

**Fixes:**

**A. Verify Service Mesh Configuration**
- **Istio Example:**
  ```yaml
  apiVersion: networking.istio.io/v1alpha3
  kind: VirtualService
  metadata:
    name: my-service
  spec:
    hosts:
    - my-service
    http:
    - route:
      - destination:
          host: my-service
          subset: v1
        weight: 90
      - destination:
          host: my-service
          subset: v2
        weight: 10
  ```
- **Action:** Check weights and subsets.

**B. Disable Sticky Sessions**
- **Kubernetes Service:**
  ```yaml
  sessionAffinity: None  # Disable sticky sessions
  ```
- **NGINX Ingress:**
  ```nginx
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  # Remove "preserve_client_address" if present
  ```

**C. Monitor Traffic Distribution**
- **Tools:** Prometheus + Grafana (track `istio_requests_total` by version).
- **Command (Kubernetes):**
  ```sh
  kubectl get pods -o wide | grep my-service
  kubectl describe svc my-service
  ```

---

## Debugging Tools & Techniques

### 1. **Logging & Observability**
- **Tools:**
  - **Logs:** `kubectl logs`, ELK Stack (Elasticsearch, Logstash, Kibana).
  - **Metrics:** Prometheus + Grafana.
  - **Traces:** Jaeger, Zipkin.
- **Quick Checks:**
  ```sh
  # Check logs for all pods in deployment
  kubectl logs -l app=my-app --tail=50 --previous

  # Filter logs by error
  kubectl logs -l app=my-app --grep="ERROR"

  # Stream logs in real-time
  kubectl logs -f <pod-name>
  ```

### 2. **Health Checks & Probes**
- **Verify Probes:**
  ```sh
  kubectl describe pod <pod-name> | grep -A 10 "Liveness:"
  ```
- **Test Endpoints Manually:**
  ```sh
  kubectl exec -it <pod-name> -- curl -v http://localhost:8080/health
  curl -H "Host: my-service" http://<ingress-ip>/health
  ```

### 3. **Network Diagnostics**
- **Check Connectivity:**
  ```sh
  # Test DB connectivity from pod
  kubectl exec -it <pod-name> -- ping db

  # Check DNS resolution
  kubectl exec -it <pod-name> -- nslookup db

  # Test external API calls
  kubectl run -it --rm curl-test --image=curlimages/curl -- sh -c 'curl -v http://external-api'
  ```

- **Service Mesh Debugging (Istio):**
  ```sh
  kubectl exec -it $(kubectl get pod -l istio=sidecar-injector -o jsonpath='{.items[0].metadata.name}') -- istioctl proxy-status
  kubectl exec -it $(kubectl get pod -l istio=sidecar-injector -o jsonpath='{.items[0].metadata.name}') -- istioctl proxy-config listeners <pod-name>
  ```

### 4. **Rollout Comparison**
- **Compare Revisions:**
  ```sh
  kubectl rollout history deployment/my-app
  kubectl get pods -l app=my-app -o wide
  ```
- **Compare ConfigMaps/Secrets:**
  ```sh
  kubectl diff configmap my-config --field-manager=kubernetes
  ```

### 5. **Performance Profiling**
- **Tools:**
  - `kubectl top pods` (for CPU/memory).
  - `pprof` (for Go applications).
  - Flame graphs (for Python/Java).
- **Example (Go pprof):**
  ```sh
  kubectl exec -it <pod-name> -- go tool pprof http://localhost:6060/debug/pprof/profile
  ```

---

## Prevention Strategies

### 1. **Infrastructure-Level**
- **Use Canary Deployments by Default:**
  ```yaml
  # Example: 10% canary rollout
  strategy:
    rollingUpdate:
      maxSurge: 10%
      maxUnavailable: 0
  ```
- **Automated Rollback Triggers:**
  - **Prometheus Alert:**
    ```yaml
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.01
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate: {{ $labels.pod }}"
        runbook_url: "https://docs.example.com/runbooks/errors"
    ```
  - **Action:** Link alerts to auto-rollback (e.g., via Argo Rollouts).

### 2. **Code-Level**
- **Feature Flags:**
  - **Service:** LaunchDarkly, Flagsmith.
  - **Example (Python with Flagsmith):**
    ```python
    from flagsmith import Client

    client = Client("YOUR_API_KEY")
    is_feature_enabled = client.get("new_dashboard", False)

    if is_feature_enabled:
        # Enable new UI
        pass
    ```

- **Backward-Compatible APIs:**
  - **Strategy:** Use versioned endpoints (e.g., `/v1/endpoint`, `/v2/endpoint`).
  - **Example (JSON schema):**
    ```json
    # v1
    {"name": "Alice", "age": 30}

    # v2 (backward-compatible)
    {"name": "Alice", "age": 30, "preferences": {}}
    ```

### 3. **Database-Level**
- **Transaction Isolation:**
  - Use `READ COMMITTED` or `SERIALIZABLE` for migrations.
- **Schema Evolution:**
  - **Tools:** Schema Spy, Flyway, Liquibase.
  - **Example (Flyway):**
    ```bash
    flyway migrate -url=jdbc:postgresql://db:5432/mydb -user=user -password=pass -locations=filesystem:migrations
    ```

### 4. **Testing**
- **Pre-Deploy Checks:**
  - **Smoke Tests:** Automated health checks before traffic shift.
    ```sh
    # Example: Test in staging
    curl -s http://staging-my-app/health | grep "OK"
    ```
  - **Chaos Engineering:** Use tools like Gremlin to test failure scenarios.
- **Post-Deploy Monitoring:**
  - **SLOs:** Define error budgets (e.g., <1% errors for new versions).
  - **Example (Error Budget):**
    ```plaintext
    Max errors for 90% traffic: 9 errors (1%)
    ```

### 5. **Documentation & Runbooks**
- **Deployment Runbook:**
  - **Steps:**
    1. Verify database migrations are ready.
    2. Update ConfigMaps/Secrets.
    3. Trigger rollout with `kubectl rollout restart`.
    4. Monitor traffic with `kubectl get svc`.
    5. Rollback if errors exceed threshold.
- **Example Rollback Command:**
  ```sh
  # Rollback to last stable revision
  kubectl rollout undo deployment/my-app --to-revision=2

  # Verify rollback
  kubectl get pods -l app=my-app -o wide
  curl -v http://my-service/health
  ```

---

## Step-by-Step Troubleshooting Workflow

Follow this checklist for rapid resolution:

1. **Reproduce the Issue:**
   - Confirm symptoms (e.g., `kubectl get pods -w`).
   - Check logs: `kubectl logs --previous <pod-name>`.

2. **Isolate the Component:**
   - Is it the **new version**? Test old version traffic.
   - Is it a **dependency**? Check DB/cache connectivity.
   - Is it **network-related**? Test from pod: `kubectl exec -it <pod> -- curl <endpoint>`.

3. **Verify Configurations:**
   - Check `maxSurge`/`maxUnavailable` in deployments.
   - Validate health probes and readiness checks.
   - Review service mesh traffic splits (if applicable).

4. **Rollback Strategically:**
   - For canary deployments: `kubectl rollout undo -n <namespace> deployment/<name> --to-revision=<stable-revision>`.
   - For full rollouts: `kubectl rollout undo deployment/<name>`.

5. **Prevent Recurrence:**
   - Add feature flags for new features.
   - Implement automated rollback on error spikes.
   - Test database migrations in staging.

---

## Example Debugging Session: Partial Outage

**Scenario:**
- Users report `503` errors for 20% of traffic.
- New version (`v2`) is at 30% traffic split.

**Steps:**
1. **Check Pods:**
   ```sh
   kubectl get pods -l app=my-app -o wide
   # Shows 3/10 pods in CrashLoopBackOff (v2).
   ```
2. **Inspect Failed Pods:**
   ```sh
   kubectl logs <failed-pod> --previous
   # Output: "Failed to connect to DB: connection refused"
   ```
3. **Verify DB Connection:**
   ```sh
   kubectl exec -it <healthy-pod> -- bash -c "ps