# **[Pattern] Deployment Gotchas: Reference Guide**

---

## **Overview**
Deployments—even seemingly routine ones—can introduce subtle failures due to misconfigurations, unconsidered edge cases, or overlooked environmental differences. The **"Deployment Gotchas"** pattern is a **proactive checklist** of common pitfalls that can derail deployments, ensuring teams anticipate issues before they impact users. This guide categorizes critical gotchas by deployment phase (e.g., pre-deployment, execution, post-deployment) and provides actionable mitigations.

Key principles:
- **Prevention over reaction**: Identify hidden risks before deployment.
- **Environment parity**: Ensure staging/test environments mirror production.
- **Rollback readiness**: Plan for quick recovery from failures.
- **Observability**: Monitor critical paths post-deployment.

Use this pattern to reduce downtime, validate configurations, and align teams on deployment expectations.

---

## **Schema Reference**
Below are high-level categories of deployment gotchas, organized by lifecycle stage. Each row includes:
- **Category**: Deployment phase or system component.
- **Gotcha**: Specific failure mode.
- **Impact**: Common consequences if unaddressed.
- **Mitigation**: Proactive solution or tooling.

| **Category**          | **Gotcha**                                                                 | **Impact**                                                                 | **Mitigation**                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Pre-Deployment**    | **Unvalidated configuration drift**                                        | Production env differs from staging, leading to runtime errors.            | Use **Infrastructure-as-Code (IaC)** (e.g., Terraform, Pulumi) to enforce consistency. Add pre-deploy checks (e.g., `terraform validate`, `kubectl diff`).                                                                          |
|                       | **Dependency version mismatches**                                         | Compatibility issues (e.g., libraries, OS packages) break services.        | Pin versions in `package.json`, `Dockerfile`, or CI/CD pipelines. Use **dependency scanning** (e.g., Snyk, Dependabot).                                                                                                                      |
|                       | **Missing or incorrect secrets/keys**                                     | Authentication failures, data leaks, or service outages.                   | Rotate secrets pre-deploy; use **secret managers** (e.g., HashiCorp Vault, AWS Secrets Manager) with automated rotation. Enforce **least privilege** access.                                                                                     |
|                       | **Rollback plan gaps**                                                     | No revert mechanism for critical failures.                                 | Document **rollback procedures** (e.g., delete/redeploy pods, revert DB migrations). Test rollbacks in staging.                                                                                                                                   |
| **Execution**         | **Network partitioning (split-brain)**                                    | Inconsistent cluster states (e.g., Kubernetes `podDisruptionBudget` misconfig). | Use **liveness/readiness probes**, **circuit breakers**, and **health checks**. Monitor with Prometheus/Grafana.                                                                                                                          |
|                       | **Resource starvation (CPU/memory)**                                       | Pods crash or throttle, degrading performance.                            | Set **resource requests/limits** in Kubernetes. Use **auto-scaling** (HPA, Cluster Autoscaler). Monitor via **cAdvisor** or **cloud-native metrics**.                                                                                  |
|                       | **Cascading failures (e.g., DB locks)**                                    | A single service failure halts dependent systems.                          | Design for **resilience**: implement retries (exponential backoff), **circuit breakers** (Hystrix/Resilience4j), and **queue-based decoupling**.                                                                                          |
|                       | **Timezone/DST conflicts**                                                 | Schedulers, cron jobs, or timezone-sensitive apps fail.                    | Standardize on **UTC** for all time-based logic. Test DST transitions in staging.                                                                                                                                          |
| **Post-Deployment**   | **Unmonitored metrics/alerts**                                           | Undetected performance degradation or errors.                              | Define **SLOs/SLIs** (e.g., latency <500ms) and set alerts (e.g., Prometheus Alertmanager). Use **distributed tracing** (Jaeger, OpenTelemetry) for latency analysis.                                                                   |
|                       | **Expired certificates/TLS**                                              | Services become unavailable or vulnerable.                                | Set **TLS renewal alerts** (e.g., 30-day warnings). Automate certificate rotation (e.g., Let’s Encrypt + cert-manager).                                                                                                             |
|                       | **Data desync (eventual consistency)**                                    | Inconsistent reads/writes across regions (e.g., multi-region DBs).         | Use **conflict-free replicated data types (CRDTs)** or **synchronous replication** where possible. Audit with **change data capture (CDC)** tools (e.g., Debezium).                                                                   |
|                       | **Unpatched vulnerabilities**                                             | Exploitable security flaws in deployed code/libraries.                     | Scan for vulnerabilities pre-deploy (e.g., **Trivy**, **OWASP ZAP**). Enforce **automated patching** (e.g., GitHub Dependabot, CVE monitoring).                                                                                     |
| **Tooling/Governance**| **Lack of deployment freeze windows**                                     | Uncontrolled traffic spikes or disruptive changes during critical periods. | Define **maintenance windows** and **traffic shifting** (blue-green, canary). Use **feature flags** to isolate changes.                                                                                                                     |
|                       | **Unclear ownership of deployments**                                     | No one is accountable for fixes.                                          | Assign **deployment owners** (e.g., SREs, on-call teams). Use **runbooks** for common failure scenarios.                                                                                                                                   |

---

## **Query Examples**
Use these queries to detect or validate mitigations for gotchas. Adjust tools (e.g., `jq`, `kubectl`, `aws cloudtrail`) as needed.

### **1. Check for Unused Secrets (Pre-Deployment)**
```bash
# List AWS Secrets Manager secrets not referenced in CloudFormation
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue="CreateSecret" \
  | jq -r '.Events[].requestParameters.secretName' \
  | grep -v "test-"  # Exclude test secrets
```

### **2. Validate Kubernetes Resource Limits (Execution)**
```bash
# Find pods without CPU/memory limits
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[0].resources}{"\n"}{end}' \
| jq -r '.[] | select(.limits == null or .requests == null) | "\(.metadata.namespace)/\(.metadata.name)"'
```

### **3. Detect Expired TLS Certificates (Post-Deployment)**
```bash
# Use certbot to check certificates (requires certbot-plugin-acme)
certbot certificates | grep EXPIRY_TIME
# Or parse Cloudflare API:
curl "https://api.cloudflare.com/client/v4/zones/YOUR_ZONE_ID/certificates" \
  | jq -r '.result[].expires_on' \
  | while read date; do
      if [ $(date -d "$date" +%s) -lt $(date +%s) ]; then
        echo "⚠️ Expired cert: $date";
      fi;
    done
```

### **4. Audit Dependency Versions (Pre-Deployment)**
```bash
# Check for vulnerable npm packages (using npm-audit)
npm audit --audit-level=critical --json | jq '.results[].vulnerabilities[].path'
```

### **5. Monitor Canary Rollout Traffic (Execution)**
```bash
# Prometheus query for canary traffic (if using Istio)
sum(rate(istio_requests_total{reporter="destination", destination_service=~"my-service.*canary.*"}[5m])) by (destination_service)
```

---

## **Related Patterns**
Deployments rely on or interact with these complementary patterns:

1. **[Blue-Green Deployment](https://docs.microsoft.com/en-us/azure/architecture/patterns/blue-green-deployment)**
   - *Why*: Mitigates rollback risk by maintaining two identical environments.
   - *Gotcha Connection*: Avoids **cascading failures** (Execution) by testing new versions in parallel.

2. **[Feature Flags](https://martinfowler.com/articles/feature-toggles.html)**
   - *Why*: Gradually roll out changes to a subset of users.
   - *Gotcha Connection*: Prevents **unmonitored metrics** (Post-Deployment) by isolating feature traffic.

3. **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)**
   - *Why*: Protects downstream services from cascading failures.
   - *Gotcha Connection*: Addresses **network partitioning** (Execution) by failing fast.

4. **[Chaos Engineering](https://chaosengineering.io/)**
   - *Why*: Proactively test resilience to failures.
   - *Gotcha Connection*: Validates mitigations for **resource starvation** (Execution) or **data desync** (Post-Deployment).

5. **[Infrastructure as Code (IaC)](https://www.terraform.io/)**
   - *Why*: Ensures environment consistency.
   - *Gotcha Connection*: Prevents **configuration drift** (Pre-Deployment) and **missing secrets**.

---
## **Best Practices Checklist**
1. **Pre-Deploy**:
   - [ ] Run **end-to-end integration tests** in staging.
   - [ ] Validate **secrets/credentials** are rotated and accessible.
   - [ ] Verify **resource requests/limits** match production needs.
   - [ ] Test **rollback procedure** in staging.

2. **Deploy**:
   - [ ] Use **canary/release trains** for high-risk changes.
   - [ ] Monitor **key metrics** (latency, error rates) during rollout.
   - [ ] Set **automated alerts** for anomalies.

3. **Post-Deploy**:
   - [ ] Review **failure logs** and update runbooks.
   - [ ]Rotate **certificates/secrets** within 1–3 months.
   - [ ] Conduct **blame-free postmortems** for any issues.

---
**Key Takeaway**: Deployment gotchas are **predictable**, not random. By systematically addressing the schema above and integrating checks into CI/CD pipelines, teams can shift left on reliability. Use the query examples to automate detection, and treat the related patterns as guardrails.