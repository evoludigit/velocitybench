# **[Pattern] Hybrid Strategies Reference Guide**

## **Overview**
The **Hybrid Strategies** pattern combines two or more discrete strategies—such as **feature toggles**, **canary deployments**, **blue-green deployments**, **A/B testing**, or **shadow releases**—to achieve more nuanced control over software delivery, rollback mechanisms, and user experience experimentation. Unlike standalone strategies, hybrid approaches allow teams to balance risk mitigation, user impact, and incremental validation simultaneously.

This pattern is ideal for scenarios where:
- **Fine-grained control** is required (e.g., progressive rollouts with fallback safety nets).
- **Multiple stakeholder objectives** must be balanced (e.g., business testing vs. stability).
- **Legacy and modern systems** need to coexist during transitions.
- **Real-time adjustments** are necessary based on performance or user feedback.

By leveraging hybrid strategies, engineers can reduce blast radius, gather data, and ensure resilience while iterating faster than monolithic deployments allow.

---

## **Schema Reference**
Hybrid strategies are constructed from a **combination of core components**, each with configurable parameters. Below is a schema breakdown:

| **Component**               | **Description**                                                                                     | **Required Config**                                                                                     | **Common Use Cases**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Primary Strategy**        | The main deployment or experimentation strategy (e.g., canary, blue-green).                           | Strategy type (e.g., "Canary", "A/BTest"), traffic allocation weights, routing rules.                     | Defines the primary flow of production traffic.                                                        |
| **Secondary Strategy**      | A fallback or complementary strategy (e.g., feature toggle, shadow release).                         | Enabled/disabled state, toggle conditions (e.g., "feature_flag = true"), shadow mode settings.          | Provides graceful degradation or parallel testing.                                                     |
| **Rollback Mechanism**      | Automated or manual rollback triggers (e.g., error rate > X%, latency spike).                       | Thresholds, fallback version, alerting integration (e.g., Prometheus, Datadog).                           | Ensures safety during hybrid transitions.                                                              |
| **Traffic Splitting Rules** | Dynamic rules to distribute traffic between strategies (e.g., 90% canary, 5% blue-green, 5% toggle).    | Weighted percentages, user segment filters (e.g., "region=us-west"), time-based sliders.                | Balances experiment reach and stability.                                                               |
| **Observability Layer**     | Tools to monitor hybrid strategy performance (metrics, logs, session replay).                       | Dashboards (Grafana), error tracking (Sentry), custom metrics (e.g., "conversion_rate").                | Validates hybrid outcomes and identifies anomalies.                                                     |
| **Canary Analysis**         | Statistical validation for canary releases (e.g., hypothesis testing, confidence intervals).        | Baseline metrics (pre-canary), statistical method (e.g., "t-test"), significance threshold (p < 0.05).   | Reduces false positives in canary rollouts.                                                            |
| **Feature Toggle Conditions** | Rules for toggles (e.g., "admin_only", "geo_restricted").                                           | Toggle keys, permissions, environment filters.                                                          | Enables conditional experiments or temporary feature gating.                                           |
| **Shadow Mode**             | Parallel processing without user impact (e.g., shadow releases for new APIs).                       | Shadow enabled flag, sampling rate, response logging.                                                   | Validates backend changes without affecting UX.                                                          |
| **User Feedback Loop**      | Mechanisms to collect user responses (e.g., surveys, in-app feedback).                              | Feedback channels, scoring (e.g., "likelihood_to_recommend"), integration (e.g., Mixpanel).             | Adjusts hybrid experiments based on qualitative data.                                                  |

---

## **Implementation Details**
Hybrid strategies require coordination between **infrastructure**, **application code**, and **observability tools**. Below are key implementation patterns:

### **1. Architectural Patterns**
| **Pattern**               | **Description**                                                                                     | **Example**                                                                                              |
|---------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Service Mesh Integration** | Use Istio/Linkerd to dynamically route traffic between strategies (e.g., canary + toggle).          | Canary: 10% traffic to `v2`, toggle: `feature_x` enabled only for `v2`.                                  |
| **Proxy-Based Routing**    | NGINX, Envoy, or Cloudflare implement hybrid logic (e.g., header-based routing to shadow releases).   | Header `X-Experiment: shadow` directs traffic to a shadowed backend.                                    |
| **Database Sharding**      | Split user segments across strategies (e.g., canary users in a dedicated DB shard).                  | Users with `canary=true` flag hit a separate shard for experimentation.                                  |
| **Serverless Hybrid**      | AWS Lambda@Edge or Cloud Run Jobs combine A/B testing with feature toggles.                          | Route 30% traffic via Lambda function to toggle `new_ui`, rest to default.                               |

### **2. Code-Level Implementation**
Hybrid strategies often involve:
- **Dynamic configuration loading** (e.g., from feature management tools like LaunchDarkly or Unleash).
- **Conditional logic** in application code to respect hybrid rules:
  ```python
  # Example: Hybrid of Canary + Feature Toggle
  def get_user_experience(user_id: str, request: HttpRequest) -> str:
      is_canary = is_user_in_canary(user_id)  # Check canary segment
      feature_enabled = is_feature_toggle_enabled(user_id, "new_dashboard")  # Check toggle

      if is_canary and feature_enabled:
          return "canary+feature"  # Hybrid path
      elif is_canary:
          return "canary_only"
      elif feature_enabled:
          return "toggle_only"
      else:
          return "default"
  ```
- **Header injection** for downstream services:
  ```http
  # Request headers for shadow mode
  X-Shadow-Mode: enabled
  X-Canary-Version: v2.1
  ```

### **3. Observability Integration**
Hybrid strategies demand **real-time monitoring**:
- **Metrics**:
  - `hybrid_error_rate`: Error rates across strategies.
  - `user_segment_conversion`: Performance by segment (e.g., canary vs. green).
  - `toggle_usage`: How often a feature toggle is triggered.
- **Logs**:
  - Sample payloads for shadow mode (e.g., `{ "shadow_mode": true, "api_version": "v3" }`).
  - Feature toggle decisions (e.g., `{ "toggle_key": "new_ui", "decision": "on" }`).
- **Tracing**:
  - Distributed tracing (Jaeger, OpenTelemetry) to correlate hybrid paths across services.

---

## **Query Examples**
Hybrid strategies introduce complexity to querying data. Below are **SQL-like pseudo-queries** and **tool-specific examples** for analyzing hybrid deployments:

### **1. Canary + Toggle Hybrid Analysis**
**Goal**: Compare conversion rates between canary users (with toggle enabled) vs. green users (toggle disabled).
```sql
SELECT
    strategy,
    COUNT(user_id) AS users,
    SUM(checkout_complete) AS conversions,
    (SUM(checkout_complete) * 100.0 / COUNT(user_id)) AS conversion_rate
FROM user_events
WHERE
    event_time > '2023-10-01'
    AND (
        (strategy = 'canary' AND feature_toggle = 'enabled') OR
        (strategy = 'green' AND feature_toggle = 'disabled')
    )
GROUP BY strategy
ORDER BY conversion_rate DESC;
```

**Tool-Specific**:
- **BigQuery**:
  ```sql
  SELECT
    IF(EXPERIMENT = 'canary', 'Canary+Toggle', 'Green')
    AS strategy,
    COUNT(userId) AS users,
    SUM(CASE WHEN action = 'purchase' THEN 1 ELSE 0 END) AS purchases
  FROM `project.dataset.user_actions`
  WHERE timestamp > TIMESTAMP('2023-10-01')
  GROUP BY strategy;
  ```
- **PostgreSQL with JSONB**:
  ```sql
  SELECT
    strategy,
    COUNT(*) AS users,
    SUM(metrics->>'conversion')::numeric AS total_conversion
  FROM (
    SELECT
      strategy,
      metrics->>'conversion' AS conversion
    FROM user_sessions
    WHERE jsonb_path_exists(metadata, '$.hybrid.enabled')
  ) AS hybrid_data
  GROUP BY strategy;
  ```

### **2. Rollback Trigger Analysis**
**Goal**: Identify if a hybrid strategy caused a spike in 5xx errors.
```sql
SELECT
    strategy,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS errors,
    COUNT(*) AS total_requests,
    ROUND(SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS error_rate
FROM hybrid_metrics
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '5 minutes'
GROUP BY strategy
HAVING error_rate > 1.0;  -- Alert if >1% errors
```

**Tool-Specific**:
- **Prometheus**:
  ```promql
  # Alert if canary+toggle error rate exceeds baseline
  (rate(http_requests_total{strategy="canary+toggle"}[5m])
    /
    rate(http_requests_total{strategy="canary+toggle",status=~"5.."}[5m])
    ) > 0.01
  ```
- **Datadog**:
  ```
  metrics.query:
    query: 'sum:aws.elb.HTTPCode_Target_5XX_Count by {env,strategy} > 10'
    filter: '@env:prod AND @strategy:canary+toggle'
  ```

### **3. Shadow Mode Latency Comparison**
**Goal**: Compare latency between shadow mode (v3) and production (v2).
```sql
SELECT
    version,
    AVG(response_time_ms) AS avg_latency,
    COUNT(*) AS requests,
    PERCENTILE_CONT(response_time_ms, 0.95) AS p95_latency
FROM api_logs
WHERE
    (version = 'v2' AND shadow_mode = false) OR
    (version = 'v3' AND shadow_mode = true)
GROUP BY version;
```

---

## **Related Patterns**
Hybrid strategies often interact with or extend these complementary patterns:

| **Related Pattern**         | **Connection to Hybrid Strategies**                                                                                     | **When to Combine**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **[Feature Toggles](https://docs.google.com/document/d/1XXt1E6W2d)** | Toggles provide conditional activation within hybrid strategies (e.g., canary users get toggle enabled).               | Use when toggles refine a canary’s feature scope.                                                        |
| **[Canary Releases](https://docs.google.com/document/d/2YYx4x1N1)** | Canary is often the primary strategy in hybrids, with toggles/shadows acting as secondaries.                        | Combine for gradual rollouts with fallback safety.                                                      |
| **[Blue-Green Deployments](https://docs.google.com/document/d/3ZZz5y7K2)** | Blue-green can coexist with canary (e.g., 90% canary, 10% blue-green for critical paths).                            | Ideal for major version upgrades with hybrid validation.                                                 |
| **[Shadow Releases](https://docs.google.com/document/d/4AAa6BBk3)** | Shadow releases validate backend changes without user traffic; can pair with canary for parallel testing.             | Use before/after canary rolls to catch hidden bugs.                                                      |
| **[A/B Testing](https://docs.google.com/document/d/5BBb7CCk4)** | A/B tests can overlay hybrid strategies (e.g., canary users in A/B group X).                                        | Combine for experiment rigor with minimal blast radius.                                                 |
| **[Progressive Delivery](https://docs.google.com/document/d/6CCd8Ef19)** | Progressive delivery is the overarching framework for hybrids; can include canary, toggles, and blue-green.          | Use for CI/CD pipelines requiring multiple validation stages.                                            |
| **[Chaos Engineering](https://docs.google.com/document/d/7DDf9Gh20)** | Inject chaos (e.g., kill 50% of canary pods) to test hybrid resilience.                                           | Validates rollback mechanisms in hybrid environments.                                                     |
| **[Service Mesh](https://docs.google.com/document/d/8Ee3w2Hk5)** | Istio/Linkerd enable dynamic hybrid routing (e.g., virtual services for canary + toggle).                           | Critical for Kubernetes-based hybrid deployments.                                                         |

---
## **Best Practices**
1. **Start Small**: Begin with **one primary strategy** (e.g., canary) and add a secondary (e.g., toggle) for specific use cases.
2. **Define Rollback Criteria**: Automate rollback for hybrid strategies (e.g., "if canary+toggle error rate > 2%, revert").
3. **Segment Users Clearly**: Avoid overlap in segments (e.g., don’t assign users to both canary and green simultaneously).
4. **Monitor Hybrid-Specific Metrics**: Track cross-strategy metrics (e.g., "canary+toggle conversion vs. canary-only").
5. **Document Hybrid Logic**: Use comments or tools like **LaunchDarkly** to clarify why a user falls into a hybrid path.
6. **Phase Out Stranded Users**: Ensure users in legacy strategies (e.g., green) are eventually migrated to hybrid paths.
7. **Test Hybrid Failures**: Simulate network partitions or toggles flipping to test resilience.

---
## **Anti-Patterns**
| **Anti-Pattern**               | **Risk**                                                                                          | **Mitigation**                                                                                           |
|---------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Overlapping Segments**        | Users assigned to multiple strategies (e.g., canary + green) cause inconsistent UX.               | Enforce mutually exclusive segments (e.g., "user_id % 100 < 10 → canary").                                |
| **Ignoring Toggle Decay**       | Feature toggles left enabled after canary success lead to unnecessary complexity.                 | Automate toggle decay post-validation.                                                                    |
| **No Observability for Hybrids** | Hybrid-specific metrics (e.g., "canary+toggle p99 latency") are missed.                           | Instrument all hybrid paths with dedicated dashboards.                                                    |
| **Hardcoded Hybrid Logic**      | Logic baked into code (e.g., `if (user_is_canary && feature_x)`) becomes fragile.                | Offload rules to feature management tools.                                                                |
| **No Rollback Plan**            | Hybrid failures (e.g., toggle misconfiguration) lack automated recovery.                          | Define pre-deployment rollback scripts.                                                                   |
| **Shadow Mode Overload**        | Shadowing too much traffic increases backend load without user benefit.                          | Limit shadow sampling (e.g., 5% of traffic).                                                              |
| **Ignoring User Feedback**      | Hybrid experiments ignore qualitative data (e.g., surveys) from affected users.                   | Integrate feedback loops into hybrid analytics.                                                          |

---
## **Tools Supporting Hybrid Strategies**
| **Category**               | **Tools**                                                                                          | **Key Features**                                                                                         |
|----------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Feature Management**     | LaunchDarkly, Unleash, Flagsmith, OpenFeature                                               | Toggles, hybrid segment control, SDKs for multiple languages.                                            |
| **Canary Deployments**     | Flagger (K8s), Argo Rollouts, Google Anthos, AWS CodeDeploy                                   | Progressive delivery, canary analysis, automated rollback.                                                |
| **Blue-Green**             | Kubernetes ArgoRollouts, AWS CodeDeploy, Heroku, GitHub Actions                               | Zero-downtime swaps, traffic shifting.                                                                    |
| **Shadow Releases**        | Service Mesh (Istio, Linkerd), NGINX, Cloudflare, AWS Lambda@Edge                             | Header-based shadow routing, sampling, parallel execution.                                                 |
| **Observability**          | Prometheus + Grafana, Datadog, New Relic, OpenTelemetry                                      | Hybrid-specific dashboards, anomaly detection, distributed tracing.                                       |
| **A/B Testing**            | Optimizely, Google Optimize, VWO, AB Tasty                                                | Statistical testing, hybrid experiment design.                                                            |
| **CI/CD Pipelines**        | GitLab CI, Jenkins, CircleCI, Argo Workflows                                                | Multi-stage hybrid deployments, approval gates.                                                          |
| **Database Sharding**      | CockroachDB, Vitess, AWS Aurora, MongoDB Sharding                                            | Isolated segments for hybrid strategies.                                                                  |

---
## **Example Workflow: Hybrid Canary + Toggle**
**Scenario**: Roll out a new checkout flow (canary) with a feature toggle for admins.

1. **Define Segments**:
   - **Canary**: 10% of users (`user_id % 100 < 10`).
   - **Toggle**: Admins only (`role = "admin"`).

2. **Implementation**:
   - **Primary Strategy**: Canary (10% traffic to `checkout_v2`).
   - **Secondary Strategy**: Toggle (`admin_only` enables new UI for admins in canary).
   - **Rollback**: If `checkout_v2` error rate > 1% for canary, revert all traffic.

3. **Query Post-Deployment**:
   ```sql
   -- Compare canary (with/without toggle) vs. green
   SELECT
     strategy,
     COALESCE(toggle_enabled, false) AS admin_toggle,
     COUNT(user_id) AS users,
     SUM(checkout_success) AS successes
   FROM user_checkouts
   WHERE event_time > '2023-10-01'
   GROUP BY strategy, toggle_enabled
   ORDER BY users DESC;
   ```

4. **Tools Used**:
   - **Feature Toggle**: LaunchDarkly (admin role check).
   - **Canary**: Argo Rollouts (10% traffic shift).
   - **Observability**: Prometheus (error rate alerting), Grafana (dashboard).
   - **Database**: CockroachDB (sharded canary users).

---
## **Further Reading**
- [Progressive Delivery at Scale (Netflix)](https://netflixtechblog.com/progressive-delivery-638371b90778)
- [Feature Flags Anti-Patterns (