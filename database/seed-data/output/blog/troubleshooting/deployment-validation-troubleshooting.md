# **Debugging Deployment Validation: A Troubleshooting Guide**
**Last Updated:** [Insert Date]
**Applicability:** microservices, CI/CD pipelines, infrastructure-as-code (IaC), Kubernetes, cloud deployments (AWS/GCP/Azure)
**Goal:** Ensure deployments meet business requirements before production traffic.

---

## **1. Overview of Deployment Validation**
Deployment Validation ensures new releases are **correct, functional, and non-regressive** before live traffic hits them. Common validation techniques include:
- **Health checks** (liveness/readiness probes)
- **Unit/integration/e2e tests** (automated or manual)
- **Canary/blue-green deployments** (traffic-based validation)
- **Monitoring/alerting** (post-deployment anomaly detection)
- **Rollback mechanisms** (automated or manual)

---

## **2. Symptom Checklist**
Before diving into fixes, confirm if the issue aligns with **Deployment Validation failures**. Check for:

| **Symptom**                          | **Likely Cause**                          | **Action Required**                     |
|--------------------------------------|-------------------------------------------|-----------------------------------------|
| ✅ Deployed but application crashes  | Misconfigured health checks, missing env vars | Check logs, validate config maps/secrets |
| ✅ Tests pass locally but fail in CI | Environment mismatch (DB, network, secrets) | Use identical test environments         |
| ✅ Slow/failed API responses          | Dependency version skew, DB schema drift  | Compare deployed vs. expected versions  |
| ✅ High error rates post-deployment   | Traffic misrouting, missing canary checks  | Verify canary percentages, network ACLs |
| ✅ Rollback triggers unexpectedly    | Overly permissive rollback rules          | Tighten conditions (e.g., error rate > 5%) |
| ✅ Metrics/spikes post-deployment    | Missing observability or validation gates  | Add prometheus/grafana alerts           |
| ✅ Secrets/config mismatches          | Incorrect YAML/Helm variables             | Validate via `kubectl get cm`/`secrets`  |

---

## **3. Common Issues and Fixes**
### **Issue 1: Health Checks Failing (Liveness/Readiness)**
**Symptom:** Pods are `CrashLoopBackOff` or `Pending` due to failing health checks.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                          | **Code Fix Example**                     |
|------------------------------------|---------------------------------------------|-------------------------------------------|
| **Incorrect readiness liveness probe** | Check probe path (`/healthz`), port, timeout | ```yaml # Kubernetes Deployment spec livenessProbe: httpGet: path: /healthz port: 8080 initialDelaySeconds: 10 periodSeconds: 5 failureThreshold: 3 ```
| **DB connection issues**           | Verify DB credentials, async init delays    | ```go # Example: Wait for DB readiness var db *sql.DB var err error for i := 0; i < 10; i++ { db, err = sql.Open("postgres", "...") if err == nil { break } time.Sleep(5 * time.Second) } ```
| **Missing environment variables**   | Check `kubectl describe pod` for env var errors | ```yaml # Fix env vars in ConfigMap apiVersion: v1 kind: ConfigMap metadata: name: app-config data: DB_HOST: "prod-db.example.com" DB_PORT: "5432" ```
| **Slow startup (e.g., JAR warmup)** | Increase `initialDelaySeconds` in probes   | ```yaml readinessProbe: httpGet: path: /ready port: 8080 initialDelaySeconds: 30 # Wait for app to boot ```

---

### **Issue 2: Tests Failing in CI but Passing Locally**
**Symptom:** Unit/integration tests succeed locally but fail in GitHub Actions/GitLab CI.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                          | **Solution**                              |
|------------------------------------|---------------------------------------------|-------------------------------------------|
| **Missing test dependencies**       | CI env lacks dev tools (e.g., Docker, Terraform) | Add to CI config: ```yaml jobs: test: docker: - docker:latest services: - postgres:9.6 before_script: - apk add --no-cache pg_client ```
| **DB schema mismatch**             | Test DB is empty or version skew            | Use testcontainers or fixtures: ```python # Example: pytest fixture def test_db_connection(db_session): assert db_session.query("SELECT 1").first() is not None ```
| **Network/timezone differences**    | UTC vs. local time, missing host resolvers   | Force UTC in tests: ```python # Set timezone in pytest.ini [pytest] addopts = --env TIMEZONE=UTC ```
| **Secrets not injected in CI**      | Hardcoded secrets or missing GitHub Secrets  | Use environment variables: ```yaml # .github/workflows/test.yml env: DB_PASSWORD: ${{ secrets.DB_PASSWORD }} ```

---

### **Issue 3: Canary Deployment Traffic Misfire**
**Symptom:** Traffic is routed incorrectly (e.g., 100% to old version).

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                          | **Fix**                                  |
|------------------------------------|---------------------------------------------|-------------------------------------------|
| **Incorrect Istio/NGINX annotation** | Misconfigured `traffic-split` rules         | Verify Istio VirtualService: ```yaml apiVersion: networking.istio.io/v1alpha3 kind: VirtualService metadata: name: my-service spec: hosts: - my-service trafficPolicy: loadBalancer: simple: DONT CARE http: - route: - destination: host: my-service version: v1 weight: 50 - destination: host: my-service version: v2 weight: 50 ```
| **DNS propagation delay**          | New DNS record not propagated               | Test with `nslookup`/`dig` before canary  |
| **Session affinity issues**         | Stickiness config not applied               | Add `sessionAffinity: ClientIP` to service |

---

### **Issue 4: Rollback Triggered Unexpectedly**
**Symptom:** Rollback happens when no major issue exists.

#### **Root Causes & Fixes**
| **Cause**                          | **Debugging Steps**                          | **Fix**                                  |
|------------------------------------|---------------------------------------------|-------------------------------------------|
| **Overly sensitive error thresholds** | Alerts fire at 1% error rate               | Tune Prometheus alerts: ```yaml - alert: HighErrorRate pages: - 'team@example.com' expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01 ```
| **Missing circuit breakers**       | Cascading failures not handled              | Add Hystrix/Resilience4j: ```java @CircuitBreaker(name = "dbService", fallbackMethod = "fallback") public String callDB() { ... } public String fallback() { return "fallback-response"; } ```
| **Manual rollback triggered by ops** | Miscommunication in on-call rotation      | Document rollback procedures clearly     |

---

## **4. Debugging Tools and Techniques**
### **A. Logging and Observability**
- **Kubernetes:**
  - `kubectl logs <pod> --previous` (for crash loops)
  - `kubectl describe pod <pod>` (events, probe failures)
  - `kubectl get events --sort-by='.metadata.creationTimestamp'`
- **Distributed Tracing:**
  - Jaeger/Zipkin for latency bottlenecks.
  - Example Jaeger query: `service:my-service` + `error=true`.
- **Metrics:**
  - Prometheus + Grafana for error rates, latency, saturation.
  - Alert on `http_requests_failure_rate > 0.05`.

### **B. Automated Validation Scripts**
- **Pre-deployment checks:**
  ```bash # Example: Validate YAML before kubectl apply yq eval '.spec.replicas >= 1' deployment.yaml || exit 1 ```
- **Post-deployment smoke tests:**
  ```python # Example: Python HTTP check import requests def test_endpoint(): response = requests.get("http://my-service/api/health") assert response.status_code == 200 ```
- **Chaos Engineering (for production):**
  Use tools like **Gremlin** or **Chaos Mesh** to simulate failures during canary.

### **C. Rollback Simulation**
- Test rollback workflows manually:
  ```bash # Simulate rollback kubectl rollout undo deployment/my-service --to-revision=2 ```

---

## **5. Prevention Strategies**
### **A. Infrastructure as Code (IaC)**
- **Use Terraform/Helm with validation:**
  ```hcl # Example: Terraform validate terraform {
    required_version = ">= 1.0.0" required_providers { kubernetes = { source = "hashicorp/kubernetes" version = "2.0" } } } ```
- **Enforce Git hooks for pre-commit checks** (e.g., `pre-commit` framework).

### **B. Shift-Left Testing**
- **Run integration tests in CI** (not just unit tests).
- **Example GitHub Actions workflow:**
  ```yaml name: Validate Deployment on PR jobs: test: runs-on: ubuntu-latest steps: - uses: actions/checkout@v2 - run: docker-compose up -d postgres - run: pytest tests/integration/ ```

### **C. Canary Best Practices**
- **Start with 1-5% traffic** and increase slowly.
- **Use feature flags** to toggle canary features:
  ```java # Spring Boot feature toggle @Configuration public class FeatureFlags { @Bean public boolean isCanaryEnabled() { return System.getenv("CANARY_ENABLED") != null; } } ```

### **D. Post-Mortem Culture**
- **Document all rollbacks** in a shared wiki (Confluence/Notion).
- **Example template:**
  ```
  Incident: [Description]
  Root Cause: [e.g., "Missing liveness probe timeout"]
  Fix: [Code/Config change]
  Prevention: [e.g., "Add 30s initial delay to probes"]
  ```

### **E. Alert Fatigue Mitigation**
- **Deduplicate alerts** (e.g., suppress repeated 5xx errors for 5 mins).
- **Use SLOs (Service Level Objectives)** to avoid over-alerting:
  ```yaml # Prometheus SLO error_budget: 1% (99.9% availability target) ```

---

## **6. Quick Reference Checklist**
| **Step**                          | **Tool/Command**                          | **Expected Outcome**                     |
|------------------------------------|--------------------------------------------|-------------------------------------------|
| Check pod health                  | `kubectl get pods -o wide`                | All pods `Running`                        |
| Verify liveness/readiness probes   | `kubectl describe pod <pod>`              | No probe failures                         |
| Test API endpoints                 | `curl http://<service>:<port>/health`     | HTTP 200                                  |
| Validate canary traffic            | `kubectl get svc -n istio-system`         | Correct `traffic-split` percentages       |
| Check DB connections               | `kubectl exec -it <pod> -- psql -c "SELECT 1"` | `1` returned                             |
| Review recent rollbacks            | `kubectl rollout history deployment/<name>` | No unexpected rollbacks                   |

---

## **7. When to Escalate**
- **Critical production impact** (e.g., 100% error rate).
- **Unknown root cause after 1 hour of debugging**.
- **Rollback fails** (e.g., stuck in `Terminating` state).

**Escalation Path:**
1. **On-call engineer** (if applicable).
2. **Architecture team** (if infrastructure issue).
3. **Dev team** (if code/logic bug).

---

## **8. Further Reading**
- [Kubernetes Best Practices for Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Canary Deployments: The Definitive Guide](https://www.oreilly.com/library/view/canary-deployments/9781492045093/)
- [Prometheus SLOs Documentation](https://prometheus.io/docs/prometheus/latest/getting_started/)

---
**End of Guide.**
*Last updated: [Date]. Feedback welcome at [contact].*