---
**[Pattern] Profiling Validation Reference Guide**
*Version 1.2*
*Last Updated: [Insert Date]*

---
## **1. Overview**
The **Profiling Validation** pattern ensures that data adheres to expected characteristics (e.g., statistical ranges, structural integrity, or domain-specific rules) before subsequent processing. Unlike traditional validation (which checks syntax or constraints), profiling validation evaluates data distributions, anomalies, or patterns to assess its "health" or fitness for downstream systems. This pattern is critical in:
- **Data pipelines** (e.g., validating raw logs before ingestion).
- **AI/ML workflows** (e.g., checking dataset distributions for bias or drift).
- **Financial systems** (e.g., detecting outliers in transaction volumes).

Key objectives:
✅ Detect subtle inconsistencies (e.g., skewed distributions, missing values).
✅ Identify data "drift" over time.
✅ Reduce false positives in downstream systems.

---

## **2. Schema Reference**
Below are core components of a profiling validation schema. Fields marked with `*` are mandatory.

| **Field**               | **Type**               | **Description**                                                                 | **Example Values**                          | **Notes**                                  |
|-------------------------|------------------------|---------------------------------------------------------------------------------|--------------------------------------------|--------------------------------------------|
| `profile_id`*           | `string`               | Unique identifier for the profile (e.g., `user_sessions_v1`).                   | `"user_sessions_v1"`                       | Used to track profile versions.            |
| `data_source`*          | `string`               | Source of the data (e.g., database, API, file).                                 | `"sales_db"`, `"web_logs"`                  | Helps categorize profiles.                 |
| `validation_rules`*     | `array[object]`        | Defines rules to validate data characteristics.                                 | *[See Table 2]*                            | Rule failures trigger alerts.              |
| `expected_distribution` | `object`               | Statistical expectations (e.g., mean, std dev, percentiles).                   | `{ "mean": 100, "p95": 200 }`             | Used for anomaly detection.                |
| `sample_size`           | `integer`              | Number of records to sample for profiling (default: `1000`).                   | `500`, `10000`                             | Adjust for large datasets.                 |
| `last_validated`        | `timestamp`            | When the profile was last validated.                                            | `2023-10-15T12:00:00Z`                     | Aids in drift detection.                   |
| `status`                | `enum`                 | Current validation status (`"pass"`, `"fail"`, `"warning"`).                   | `"pass"`, `"fail:outliers"`                 | Correlates with alerts.                     |
| `metadata`              | `object`               | Additional context (e.g., team, system).                                       | `{ "owner": "data-team", "priority": "high" }` | Optional.                                  |

---

### **Table 2: Validation Rules Schema**
Rules define how data should conform to expectations.

| **Field**               | **Type**               | **Description**                                                                 | **Example**                              | **Notes**                                  |
|-------------------------|------------------------|---------------------------------------------------------------------------------|------------------------------------------|--------------------------------------------|
| `rule_id`*              | `string`               | Unique identifier for the rule (e.g., `value_range_min`).                      | `"value_range_min"`                      | Must be unique per profile.                |
| `field`*                | `string`               | Column/field to validate.                                                       | `"transaction_amount"`, `"user_age"`     | Case-sensitive if applicable.              |
| `type`*                 | `string`               | Rule type (`"range"`, `"distribution"`, `"missing"`, `"format"`, `"unique"`). | `"range"`                                | Determines validation logic.               |
| `params`*               | `object`               | Rule-specific parameters.                                                      | *[See Table 3]*                          | Varies by `type`.                          |
| `severity`              | `enum`                 | Impact level (`"critical"`, `"high"`, `"medium"`, `"low"`).                     | `"high"`                                 | Affects alerting thresholds.                |
| `last_checkpass`        | `timestamp`            | When the rule last passed validation.                                          | `2023-10-14T09:00:00Z`                   | Used for drift detection.                  |

---

### **Table 3: Rule Parameter Examples**
| **Rule Type**  | **Params Example**                                      | **Description**                                                                 |
|----------------|--------------------------------------------------------|---------------------------------------------------------------------------------|
| `range`        | `{ "min": 0, "max": 1000 }`                            | Validates values fall within `[min, max]`.                                     |
| `distribution` | `{ "mean": 100, "std_dev": 20, "p99": 200 }`          | Checks statistical properties (e.g., mean ± 2σ).                                 |
| `missing`      | `{ "threshold": 0.05 }`                                | Fails if >5% of values are missing.                                            |
| `format`       | `{ "regex": `/^\d{3}-\d{2}-\d{4}$/` }`                | Validates string format (e.g., SSN).                                           |
| `unique`       | `{ "distinct_count_min": 90 }`                        | Ensures ≥90% of values are unique.                                              |

---
## **3. Query Examples**
### **3.1 Validate a Profile**
Query to check if a profile meets all rules.

```sql
-- SQL (Pseudocode)
SELECT
  profile_id,
  data_source,
  status,
  rule_id,
  CASE
    WHEN status = 'fail' THEN error_message
    ELSE 'PASS'
  END AS validation_result
FROM validation_profiles
WHERE profile_id = 'user_sessions_v1'
ORDER BY last_validated DESC;
```

**Expected Output:**
| `profile_id`   | `data_source` | `status`      | `rule_id`           | `validation_result` |
|----------------|---------------|---------------|---------------------|---------------------|
| `user_sessions_v1` | `web_logs`   | `fail`        | `value_range_min`   | `Anomaly: 90% of values < $10` |

---

### **3.2 Detect Drift Over Time**
Query to flag profiles where rules recently failed.

```python
# Python (Pandas)
import pandas as pd

drift_profiles = (
    df.query("last_validated > '2023-10-01'")
    .groupby("profile_id")
    .filter(lambda g: (g["status"] == "fail").any())
    .sort_values("last_validated", ascending=False)
)
print(drift_profiles[["profile_id", "last_validated", "rule_id"]])
```

**Output:**
```
   profile_id last_validated      rule_id
1  user_sessions_v1 2023-10-15  value_range_min
0  order_processes  2023-10-12  missing_threshold
```

---

### **3.3 Generate Profiling Report**
Script to export profile stats to CSV.

```bash
# Bash (using jq for JSON processing)
jq -r '
  .profiles[]
  | "\(.profile_id),\(.data_source),\(.status),\(.validation_rules[].rule_id)"
' profiles.json > report.csv
```

**Output (`report.csv`):**
```
user_sessions_v1,web_logs,pass,value_range_min
order_processes,sales_db,fail,missing_threshold
```

---

## **4. Implementation Details**
### **4.1 Core Components**
1. **Profiling Engine**:
   - Libraries: Use [`Great Expectations`](https://docs.greatexpectations.io/), [`PyJanitor`](https://pyjanitor.dev/), or custom scripts (Python/R).
   - Example workflow:
     ```python
     from great_expectations.dataset import PandasDataset

     data = PandasDataset(df)
     results = data.expect_column_values_to_not_be_null("user_id")
     ```

2. **Rule Engine**:
   - Define rules in JSON/YAML (see Schema Reference).
   - Example YAML snippet:
     ```yaml
     rules:
       - rule_id: "age_range"
         type: "range"
         params: { min: 18, max: 100 }
     ```

3. **Alerting**:
   - Integrate with tools like **Slack**, **PagerDuty**, or custom webhooks.
   - Example Slack alert payload:
     ```json
     {
       "text": "⚠️ Profile `user_sessions_v1` failed rule `value_range_min`.",
       "attachments": [{"color": "#ff0000", "fields": [{"title": "Error", "value": "95% of values < $5"}]}]
     }
     ```

4. **Storage**:
   - Store profiles in databases (PostgreSQL) or time-series DBs (InfluxDB) for trend analysis.

---

### **4.2 Performance Considerations**
| **Aspect**               | **Recommendation**                                                                 |
|--------------------------|-----------------------------------------------------------------------------------|
| **Sampling**             | Profile large datasets (>1M rows) with stratified sampling to reduce compute cost. |
| **Rule Ordering**        | Prioritize `missing`/`format` rules (fast to check) before statistical rules.     |
| **Parallelization**      | Use Dask or Spark for distributed profiling of huge datasets.                     |
| **Caching**              | Cache profile results (e.g., Redis) if the data source hasn’t changed.            |

---

### **4.3 Common Pitfalls**
| **Issue**                          | **Solution**                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| Overly strict rules (false positives). | Start with loose thresholds; adjust via A/B testing.                      |
| Ignoring data drift.               | Set up alerts for rule failures over time (e.g., 3 consecutive fails).     |
| Profiling skewed data.             | Use robust statistics (median/IQR) instead of mean/std dev.                 |
| Slow validation in CI/CD.          | Run profiling in a separate stage after unit tests.                         |

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Data Quality Gateway](https://patterns.datadriven.tech/data-quality-gateway)** | Enforces validation at pipeline ingress.                     | When data enters a critical system (e.g., DB).   |
| **[Schema Evolution](https://patterns.datadriven.tech/schema-evolution)**       | Handles changing schemas gracefully.                          | When schemas drift over time.                    |
| **[Anomaly Detection](https://patterns.datadriven.tech/anomaly-detection)**  | Flags outliers in real-time.                                 | For monitoring systems (e.g., fraud detection). |
| **[Data Lineage](https://patterns.datadriven.tech/data-lineage)**              | Tracks data flow for auditing.                                | Post-profiling, for traceability.                 |

---
## **6. Next Steps**
1. **Start Small**: Profile one high-risk data source (e.g., customer data).
2. **Automate**: Integrate profiling into CI/CD (e.g., GitHub Actions).
3. **Iterate**: Adjust rules based on false positives/negatives.
4. **Extend**: Combine with **Anomaly Detection** for real-time alerts.