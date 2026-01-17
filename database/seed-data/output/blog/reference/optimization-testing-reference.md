**[Pattern] Optimization Testing Reference Guide**

---

# **Overview**
Optimization Testing is a structured pattern for identifying and validating performance bottlenecks in applications (web, mobile, APIs, or databases). This guide covers best practices for defining, implementing, and analyzing tests to reduce latency, improve resource efficiency, and enhance user experience. The pattern leverages **baseline comparisons**, **synthetic monitoring**, and **real-user metrics** to quantify improvements while avoiding false positives or over-optimization.

Optimization Testing is critical for:
- **Web/Mobile Apps**: Reducing Time to Interactive (TTI), First Contentful Paint (FCP), or Total Blocking Time (TBT).
- **APIs**: Lowering response times under load (e.g., 99th percentile latency reduction).
- **Databases**: Optimizing query execution, reducing cache miss rates, or improving throughput.
- **Infrastructure**: Scaling compute/storage efficiently under predicted traffic spikes.

Best suited for teams adopting a **continuous optimization cycle** (e.g., DevOps, SRE, or front-end engineering).

---

## **2. Schema Reference**
Define key optimization testing metrics and their attributes using this schema for consistency across tools (e.g., Lighthouse, New Relic, Kubernetes metrics, or custom scripts).

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                          | **Notes**                                  |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------------|--------------------------------------------|
| **Test Name**           | String         | Human-readable identifier (e.g., "mobile-payment-flow-optimization").           | `"checkout-v2"`                             | Aligns with CI/CD pipelines.              |
| **Target System**       | Enum           | [web, mobile, api, database, infrastructure]                                  | `"api"`                                     | Scope of optimization.                    |
| **Baseline**            | Object         | Reference metrics (collected before optimization).                            | `{ "ttb": 1.2s, "error_rate": 0.005 }      | Required for comparison.                  |
| **Optimization Change** | Object         | What was modified (e.g., code, config, infrastructure).                       | `{ "step": "enable-compression", "version": "v2.3" }` | Track changes for reproducibility. |
| **Measurement Method**  | Enum           | [synthetic, real-user, load-test, profiling]                                  | `"synthetic"`                                | Determines tooling (e.g., k6, Chrome UX Rep.). |
| **Metrics Collected**   | Array[Object]  | Key performance indicators (KPIs) to track.                                  | `[{ "name": "fcp", "unit": "ms" }, ...]`    | Include business-specific metrics.          |
| **Environment**         | Enum           | [staging, production, preprod]                                               | `"staging"`                                 | Affects load/real-user data validity.      |
| **Tooling**             | Array[String]  | Tools used (e.g., Lighthouse, Grafana, JMeter).                              | `["lighthouse", "k6"]`                     | Cross-reference with implementation steps. |
| **Result**              | Object         | Post-optimization metrics vs. baseline.                                      | `{ "improvement": -35%, "confidence": 0.95 }` | Use statistical significance thresholds.    |
| **Validation Criteria** | Array[String]  | Business rules to validate success (e.g., "reduce latency by 20%").             | `["p95_latency < 300ms"]`                  | Links to SLIs/SLOs.                        |
| **Dependencies**        | Array[String]  | Related tests, services, or configurations.                                 | `["db-scaling-test", "cache-config"]`       | Avoid siloed optimizations.                |
| **Severity**            | Enum           | [critical, high, medium, low]                                                | `"high"`                                    | Prioritization for teams.                 |
| **Tags**                | Array[String]  | Categorize by feature, team, or tech stack (e.g., "react", "payment-service").| `["frontend", "js-bundle"]`                 | Filtering in dashboards.                  |

---

## **3. Implementation Details**

### **3.1 Key Concepts**
1. **Baseline**
   - **Definition**: Initial metrics collected *before* optimization.
   - **How to Collect**:
     - **Synthetic**: Use tools like **Lighthouse CI**, **WebPageTest**, or **k6** to simulate user flows.
     - **Real User**: Integrate with **Chrome UX Report** or **New Relic** for production data.
     - **Load Testing**: Run **JMeter** or **Gatling** under predicted load (e.g., 90th percentile traffic).
   - **Tip**: Collect baselines during **peak hours** to account for variability.

2. **Change Identification**
   - **Granularity**: Test changes incrementally (e.g., optimize one CSS file first, then bundling).
   - **Isolation**: Use feature flags or canary deployments to isolate variables.
   - **Example**:
     ```json
     "optimization_change": {
       "type": "code",
       "file": "src/components/payment-button.js",
       "diff": "const _ = require('lodash/debounce');"
     }
     ```

3. **Measurement Method**
   | **Method**          | **When to Use**                          | **Tools**                          | **Pros**                                  | **Cons**                                  |
   |---------------------|-----------------------------------------|------------------------------------|-------------------------------------------|-------------------------------------------|
   | **Synthetic**       | New features, controlled environments.  | Lighthouse, k6, WebPageTest         | Repeatable, low cost.                      | Doesn’t reflect real user conditions.     |
   | **Real User**       | Production-ready validation.            | Chrome UX Rep., New Relic, Datadog | Accurate, contextual.                     | High variance, privacy concerns.          |
   | **Load Testing**    | Scaling performance under load.         | JMeter, k6, Locust                  | Identifies bottlenecks under stress.      | Requires load generation setup.            |
   | **Profiling**       | Deep-dive into CPU/memory usage.        | Chrome DevTools, Firefox Profiler  | Granular insights (e.g., JS heap usage).  | High overhead for large apps.             |

4. **Validation Criteria**
   - Define **success thresholds** tied to business goals:
     - **Web**: `"ttb < 1s"` (Google’s Core Web Vitals).
     - **API**: `"p99_latency < 500ms"` (SLO for backend teams).
     - **Database**: `"query_duration < 200ms"` (95th percentile).
   - **Statistical Significance**: Use **A/B testing** or **t-tests** to confirm improvements aren’t due to randomness.

---

### **3.2 Implementation Steps**
1. **Define Scope**
   - Identify the **user journey**, **component**, or **service** to optimize.
   - Example: *"Reduce checkout page load time by 40%."*

2. **Collect Baseline**
   - **Synthetic Example (k6 script)**:
     ```javascript
     import http from 'k6/http';
     import { check } from 'k6';

     export const options = { thresholds: { http_req_duration: ['p(95)<1000'] } };

     export default function () {
       const res = http.get('https://example.com/checkout');
       check(res, { 'status was 200': (r) => r.status === 200 });
     }
     ```
   - **Real User Example (New Relic)**:
     - Query `"Transaction/tx.startTime"` to find baseline latency percentiles.

3. **Apply Optimization**
   - Common tactics:
     - **Web/Mobile**: Lazy loading, code splitting, image optimization (e.g., `srcset`).
     - **API**: Add caching (Redis), database indexing, or query optimization.
     - **Infrastructure**: Right-size VMs, use serverless for sporadic workloads.

4. **Re-measure**
   - Run the same test post-optimization.
   - **Example Query (Prometheus)**:
     ```
     # Compare 95th percentile latency before/after optimization
     max_over_time(rate(http_request_duration_seconds{job="api-optimized"}[1m])) by (quantile)
     ```

5. **Validate Against Criteria**
   - **Pass/Fail Logic**:
     ```python
     # Pseudocode for validation
     if (new_fcp < baseline_fcp * 0.6) and p_value < 0.05:
         return "SUCCESS"
     else:
         return "FAIL"
     ```

6. **Document & Roll Back**
   - Store results in a **test report** (e.g., Markdown/JSON):
     ```json
     {
       "test_name": "checkout-page-ttb",
       "baseline_ttb": 1500,
       "post_ttb": 900,
       "improvement": 40,
       "confidence": 0.98,
       "rollback_plan": "Revert: git reset --hard HEAD~1"
     }
     ```

---

## **4. Query Examples**
### **4.1 Synthetic Testing (k6)**
**Goal**: Measure API response times under synthetic load.
```javascript
// simulate 100 users at 1 request/second
import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<300'], // 95% of requests < 300ms
    checks: ['rate>0.95']             // 95% success rate
  }
};

export default function () {
  const res = http.get('https://api.example.com/v2/search');
  sleep(1);
}
```

### **4.2 Real User Monitoring (Prometheus + Grafana)**
**Goal**: Alert on FCP degradation in production.
**Prometheus Query**:
```
# Alert if FCP increases by >20% from baseline (7-day average)
(increase(page_fcp_seconds[1h]) > avg_over_time(rate(page_fcp_seconds[1h]))[7d:1h] * 1.2)
```
**Grafana Dashboard Panel**:
- Compare `page_fcp_seconds` over time with a **baseline threshold**.
- Use **annotations** to correlate with deployments.

### **4.3 Database Query Optimization**
**Goal**: Reduce slow query percentage in PostgreSQL.
**pgBadger Report Filter**:
```bash
# Analyze slow queries (duration > 1s)
pgbadger -f postgresql.log | grep -E "duration: [1-9][0-9]+s"
```
**Optimization Checklist**:
| **Query Type**       | **Optimization**               | **Tool**                  |
|----------------------|---------------------------------|---------------------------|
| `SELECT *`           | Add `LIMIT` or columns          | `EXPLAIN ANALYZE`         |
| Missing index        | Create index on `WHERE` columns | `pg_stat_statements`      |
| N+1 queries          | Use `JOIN` or `FETCH`           | Rails `bulk_insert`       |

### **4.4 Infrastructure Scaling (Kubernetes)**
**Goal**: Right-size pod resources to reduce CPU waste.
**Metrics Query (kubectl)**:
```bash
# Find pods with high CPU usage
kubectl top pods --sort-by=cpu
```
**Optimization**:
- Use **Vertical Pod Autoscaler (VPA)**:
  ```yaml
  # deploy vpa.yaml
  apiVersion: autoscaling.k8s.io/v1
  kind: VerticalPodAutoscaler
  metadata:
    name: my-app-vpa
  spec:
    targetRef:
      apiVersion: "apps/v1"
      kind: Deployment
      name: my-app
    updatePolicy:
      updateMode: "Auto"
  ```
- **Horizontal Pod Autoscaler (HPA)** for traffic spikes:
  ```bash
  kubectl autoscale deployment my-app --cpu-percent=80 --min=2 --max=10
  ```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          | **Tools/Libraries**                     |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|------------------------------------------|
| **A/B Testing**           | Compare two variants to measure impact on user behavior/metrics.             | Evaluating optimizations in production. | Google Optimize, VWO, Optimizely        |
| **Canary Releases**       | Gradually roll out changes to a subset of users to detect issues early.      | High-risk optimizations (e.g., DB schema changes). | Istio, Flagger, LaunchDarkly          |
| **Load Testing**          | Simulate traffic to identify bottlenecks under stress.                       | Scaling infrastructure or APIs.          | JMeter, Gatling, k6                      |
| **Performance Budgeting** | Allocate performance budgets per feature to prevent regressions.              | Large teams with many simultaneous changes. | WebPageTest Budgets, SLOs                 |
| **Observability Stack**   | Centralize metrics, logs, and traces for root-cause analysis.                 | Debugging optimization failures.        | Prometheus + Grafana + Jaeger           |
| **Feature Flags**         | Toggle optimizations on/off dynamically (e.g., enable cache only for A/B users). | Safe experimentation.                   | LaunchDarkly, Unleash, Flagsmith         |

---

## **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Risk**                                  | **Mitigation**                          |
|---------------------------------------|-------------------------------------------|------------------------------------------|
| **Ignoring real user data**           | Synthetic tests may not reflect production. | Combine synthetic + RUM metrics.        |
| **Optimizing without baselines**     | No way to measure improvement.           | Always collect baselines pre/post.      |
| **Over-optimizing one metric**       | Sacrificing other KPIs (e.g., latency vs. cost). | Define multi-dimensional success criteria. |
| **No rollback plan**                  | Failed optimizations break production.  | Automate rollbacks (e.g., CI/CD pipelines). |
| **Tooling silos**                     | Inconsistent metrics across teams.        | Standardize schemas (e.g., OpenTelemetry). |
| **False positives due to noise**      | Random spikes mask real improvements.     | Use statistical tests (e.g., t-tests).  |

---
## **7. Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **TTI (Time to Interactive)** | Time until the page is fully interactive (e.g., form submissions work). |
| **FCP (First Contentful Paint)** | When the first text/logo renders.                                             |
| **TBT (Total Blocking Time)**   | Time blocked by long tasks (e.g., JS) during page load.                      |
| **SLO (Service Level Objective)** | Target metric (e.g., "99% of API calls < 500ms").                           |
| **SRE (Site Reliability Engineering)** | Balance of reliability and optimization in production.                       |
| **Jamf (Just a Minute Frame)**    | Metric for how long users must wait before interacting (e.g., "Jamf < 3s").    |
| **Quantile**            | Statistical measure (e.g., p95 = 95th percentile latency).                      |
| **Canary Analysis**      | Gradually roll out changes to detect regressions early.                       |

---
## **8. Further Reading**
- **Google’s Core Web Vitals**: [developer.chrome.com/vitals](https://developer.chrome.com/docs/lighthouse/vitals/)
- **k6 Documentation**: [k6.io/docs/](https://k6.io/docs/)
- **Optimization Case Studies**: [Webflow’s performance wins](https://webflow.com/blog/performance)
- **Observability**: [OpenTelemetry](https://opentelemetry.io/)
- **Database Tuning**: [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance.html)