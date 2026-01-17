# **[Pattern] Latency Standards Reference Guide**

---

## **1. Overview**
The **Latency Standards** pattern defines measurable targets for system response times, ensuring consistent, predictable performance across distributed systems. This pattern helps engineers and DevOps teams enforce Service Level Objectives (SLOs) by classifying latency into tiers (e.g., Critical, Important, Secondary) and setting acceptable thresholds.

Unlike generic "low latency" goals, Latency Standards provide structured benchmarks, enabling proactive monitoring, alerting, and performance tuning. It supports:
- **Prioritization**: Focus resources on high-impact paths.
- **Diagnostics**: Pinpoint bottlenecks via SLO violations.
- **Compliance**: Align with SLAs (Service Level Agreements) and business policies.

This guide covers schema definitions, query examples, and integration with related patterns.

---

## **2. Schema Reference**

### **2.1 Core Entities**

| **Entity**          | **Description**                                                                 | **Key Fields**                                                                 |
|----------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **LatencyTiers**     | Classification of response time criticality.                                   | `tier` (string: *CRITICAL*, *IMPORTANT*, *SECONDARY*), `default_slo` (duration) |
| **ServicePath**      | Endpoint or microservice interaction path.                                     | `path_id` (uuid), `description` (string), `tier` (ref: LatencyTiers.tier)   |
| **LatencyTargets**   | SLAs per path and tier.                                                          | `path_id` (ref: ServicePath), `tier` (ref: LatencyTiers.tier), `p95` (duration), `p99` (duration) |
| **PerformanceAlert** | Alerts triggered by SLO breaches.                                              | `alert_id` (uuid), `path_id` (ref: ServicePath), `threshold_violation` (bool), `timestamp` (datetime) |

### **2.2 Example Schema (SQL-like Pseudocode)**
```sql
CREATE TABLE LatencyTiers (
    tier ENUM('CRITICAL', 'IMPORTANT', 'SECONDARY') PRIMARY KEY,
    default_slo TIMESTAMP
);

CREATE TABLE ServicePath (
    path_id UUID PRIMARY KEY,
    description TEXT,
    tier VARCHAR(20) REFERENCES LatencyTiers(tier)
);

CREATE TABLE LatencyTargets (
    path_id UUID REFERENCES ServicePath,
    tier VARCHAR(20) REFERENCES LatencyTiers,
    p95 TIMESTAMP,
    p99 TIMESTAMP,
    PRIMARY KEY (path_id, tier)
);
```

### **2.3 JSON Example**
```json
{
  "service_paths": [
    {
      "path_id": "a1b2c3d4-1234-5678",
      "description": "API: /checkout",
      "tier": "CRITICAL",
      "targets": {
        "p95": "100ms",
        "p99": "200ms"
      }
    }
  ],
  "latency_tiers": {
    "CRITICAL": { "default_slo": "500ms" }
  }
}
```

---

## **3. Query Examples**

### **3.1 Fetch Latency Metrics for a Path**
```sql
-- Find all SLOs for a specific path
SELECT *
FROM LatencyTargets
WHERE path_id = 'a1b2c3d4-1234-5678';
```

**Output:**
```
| path_id            | tier      | p95   | p99   |
|--------------------|-----------|-------|-------|
| a1b2c3d4-1234-5678| CRITICAL  | 100ms | 200ms |
```

---

### **3.2 Alert on SLO Violations**
```sql
-- Check for paths exceeding p99 thresholds
SELECT p.path_id, p.description, lt.tier,
       lt.default_slo,
       MAX(CASE WHEN latency > lt.default_slo THEN TRUE ELSE FALSE END) AS violated
FROM PerformanceAlert pa
JOIN ServicePath p ON pa.path_id = p.path_id
JOIN LatencyTargets lt ON p.path_id = lt.path_id
WHERE pa.threshold_violation = TRUE
GROUP BY p.path_id;
```

**Output:**
```
| path_id            | description       | tier      | default_slo | violated |
|--------------------|-------------------|-----------|-------------|----------|
| b5c6d7e8-9012-3456 | API: /search      | IMPORTANT  | 300ms       | TRUE     |
```

---

### **3.3 Update Targets for a Tier**
```sql
-- Adjust p99 targets for 'IMPORTANT' tier
UPDATE LatencyTargets
SET p99 = '350ms'
WHERE tier = 'IMPORTANT';
```

---

## **4. Implementation Steps**

### **4.1 Define Latency Tiers**
Assign criticality to paths via `LatencyTiers`:
```sql
-- Add a new tier
INSERT INTO LatencyTiers (tier, default_slo)
VALUES ('SECONDARY', '1s');
```

### **4.2 Set Path-Specific Targets**
Create `LatencyTargets` entries:
```sql
INSERT INTO LatencyTargets (path_id, tier, p95, p99)
VALUES ('a1b2c3d4-1234-5678', 'CRITICAL', '100ms', '200ms');
```

### **4.3 Integrate Monitoring**
- **Prometheus**: Label queries with `latency_tier`:
  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, latency_tier))
  ```
- **Grafana Dashboards**: Visualize SLO violations per tier.

---

## **5. Validation & Testing**

### **5.1 Unit Tests**
```python
# Mock data for testing
def test_slo_violation():
    targets = {
        "a1b2c3d4-1234-5678": {"p95": "150ms", "p99": "250ms"}  # Violation
    }
    assert mock_monitor.check_slo(path_id="a1b2c3d4-1234-5678", observed=200ms) == False
```

### **5.2 Integration Test**
Verify alerting triggers:
```bash
# Simulate a p99 breach in a staging environment
curl -X POST http://localhost:9090/api/alerts \
  -d '{"path_id": "b5c6d7e8-9012-3456", "latency": "400ms"}'
# Expected: Alert fired for 'IMPORTANT' tier
```

---

## **6. Related Patterns**

| **Pattern**               | **Description**                                                                 | **Integration**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Circuit Breaker**       | Isolate failure cascades.                                                    | Use Latency Standards to define "failing" thresholds for circuit trips.      |
| **Rate Limiting**         | Control request volume.                                                      | Combine with Latency Standards to prioritize critical paths.                  |
| **Auto-Scaling**          | Dynamically adjust resources.                                                | Scale pods/containers based on tier violations (e.g., 10% CPU spike in CRITICAL). |
| **Distributed Tracing**   | Trace latency across services.                                               | Annotate traces with `latency_tier` for SLO correlation.                    |

---

## **7. Best Practices**

1. **Start Conservative**: Set initial SLOs 10-20% above baseline to avoid false positives.
2. **Tier Alignments**:
   - **CRITICAL**: Core user flows (e.g., checkout).
   - **IMPORTANT**: Secondary actions (e.g., search).
   - **SECONDARY**: Admin APIs (e.g., analytics).
3. **Automate Alerts**: Route violations to PagerDuty/SLACK with tier-specific escalations.
4. **Document Exceptions**: Allow transient breaches (e.g., 300ms spikes) via `slo_exceptions` table.
5. **Continuous Review**: Re-evaluate targets quarterly or after major updates.

---
**Example Exception Table:**
```sql
CREATE TABLE SLOExceptions (
    path_id UUID REFERENCES ServicePath,
    tier VARCHAR(20) REFERENCES LatencyTiers,
    start_time DATETIME,
    end_time DATETIME,
    reason TEXT
);
```