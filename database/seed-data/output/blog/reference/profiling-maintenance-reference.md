---
# **[Pattern] Reference Guide: Profiling Maintenance**

---

## **Overview**
The **Profiling Maintenance** pattern ensures long-term usability of data profiles by systematically updating, validating, and optimizing metadata schemas, business rules, and quality checks. This pattern is critical in data governance, metadata management, and ETL pipelines where schema drift or evolving business requirements can render profiles obsolete. Profiling Maintenance automates the recalibration of profiling attributes (e.g., frequency, thresholds, sampling strategies) against new data distributions, reduces manual intervention, and improves adaptability. Key use cases include:
- Adjusting data quality rules (e.g., null thresholds) for growing datasets.
- Re-evaluating statistical distributions (e.g., mean/median) for skewed data trends.
- Enriching profile metadata with new sources (e.g., regulatory fields) without breaking existing pipelines.

The pattern complements **Data Profiling** by addressing its dynamic nature, ensuring profiles remain actionable over time.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Definition**                                                                                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Profile Attributes**    | Metrics (e.g., cardinality, null rates) or rules (e.g., "numeric values > 1000 flagged") stored in a profile repository.                                         |
| **Recalibration Cycle**   | Scheduled or event-triggered process to update attributes (e.g., weekly for high-volume tables).                                                            |
| **Sampling Strategy**     | Adjustable sampling rate (e.g., 1% for large tables, 100% for small) to balance accuracy and performance.                                                        |
| **Drift Detection**       | Algorithm to compare current data stats (e.g., mean) against historical baselines to flag anomalies.                                                            |
| **Profile Repository**    | Centralized storage (e.g., database table or NoSQL collection) holding profile metadata, rules, and recalibration logs.                                          |
| **Validation Rules**      | Business logic (e.g., "column X must not exceed 95% nulls") used to enforce data standards during recalibration.                                               |

---

## **Schema Reference**
Below is a **profile repository schema** for tracking metadata and recalibration status.

### **1. `profiles.schema` (Core Metadata)**
| Column               | Type          | Description                                                                                                                                                     |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `profile_id`         | UUID (PK)     | Unique identifier for the profile (e.g., `uuid4()`).                                                                                                         |
| `entity_name`        | VARCHAR(255)  | Source table/view name (e.g., `customers`).                                                                                                                 |
| `schema_name`        | VARCHAR(255)  | Database schema (e.g., `staging`).                                                                                                                         |
| `created_at`         | TIMESTAMP     | When the profile was initially generated (immutable).                                                                                                      |
| `last_updated`       | TIMESTAMP     | Last recalibration timestamp.                                                                                                                              |
| `sampling_rate`      | DECIMAL(5,2)  | % of rows sampled (e.g., `0.01` for 1%).                                                                                                                  |
| `data_source`        | VARCHAR(50)   | Source type (e.g., `db`, `api`, `file`).                                                                                                                   |

---

### **2. `profile_attributes` (Stored Metrics)**
| Column               | Type          | Description                                                                                                                                                     |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `attribute_id`       | UUID (PK)     | Unique identifier for an attribute (e.g., `null_rate`, `distinct_count`).                                                                                 |
| `profile_id`         | UUID (FK)     | References `profiles.schema`.                                                                                                                               |
| `column_name`        | VARCHAR(255)  | Target column (e.g., `email`).                                                                                                                              |
| `data_type`          | VARCHAR(50)   | SQL data type (e.g., `VARCHAR`, `INTEGER`).                                                                                                                 |
| `metric_name`        | VARCHAR(100)  | Predefined metric (e.g., `null_rate`, `min_value`).                                                                                                      |
| `current_value`      | TEXT          | Latest computed value (e.g., `"0.07"` for 7% nulls).                                                                                                       |
| `baseline_value`     | TEXT          | Historical value for drift detection.                                                                                                                     |
| `valid_from`         | TIMESTAMP     | Timestamp of last validation (e.g., `2023-10-01 00:00:00`).                                                                                               |

---
### **3. `recalibration_logs` (Audit Trail)**
| Column               | Type          | Description                                                                                                                                                     |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `log_id`             | UUID (PK)     | Unique log entry ID.                                                                                                                                          |
| `profile_id`         | UUID (FK)     | References `profiles.schema`.                                                                                                                               |
| `action`             | VARCHAR(50)   | `RECALIBRATE`, `VALIDATE`, or `FAILURE`.                                                                                                                  |
| `executed_at`        | TIMESTAMP     | When the action occurred.                                                                                                                                      |
| `status`             | VARCHAR(20)   | `SUCCESS`, `WARNING`, or `ERROR`.                                                                                                                         |
| `error_message`      | TEXT          | Details if `status = ERROR`.                                                                                                                              |
| `new_baseline`       | TEXT          | Updated `baseline_value` post-recalibration.                                                                                                              |

---

## **Query Examples**
### **1. List Profiles Requiring Recalibration**
```sql
SELECT
    p.profile_id,
    p.entity_name,
    p.last_updated,
    DATE_DIFF(CURRENT_TIMESTAMP, p.last_updated, DAY) AS days_since_last_update
FROM profiles.schema p
WHERE DATE_DIFF(CURRENT_TIMESTAMP, p.last_updated, DAY) > 7
ORDER BY days_since_last_update DESC;
```

### **2. Check for Drift in Null Rates**
```sql
SELECT
    a.profile_id,
    a.column_name,
    a.metric_name,
    a.current_value AS current_null_rate,
    a.baseline_value AS baseline_null_rate,
    ABS(CAST(a.current_value AS DECIMAL) - CAST(a.baseline_value AS DECIMAL)) AS drift_magnitude
FROM profile_attributes a
WHERE a.metric_name = 'null_rate'
  AND ABS(CAST(a.current_value AS DECIMAL) - CAST(a.baseline_value AS DECIMAL)) > 0.05  -- 5% threshold
ORDER BY drift_magnitude DESC;
```

### **3. Generate Recalibration Report**
```sql
WITH recalibration_status AS (
    SELECT
        p.profile_id,
        p.entity_name,
        COUNT(DISTINCT r.log_id) AS total_recals,
        SUM(CASE WHEN r.status = 'ERROR' THEN 1 ELSE 0 END) AS failures
    FROM profiles.schema p
    LEFT JOIN recalibration_logs r ON p.profile_id = r.profile_id
    WHERE r.executed_at >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 30 DAY)
    GROUP BY p.entity_name
)
SELECT
    entity_name,
    total_recals,
    failures,
    (failures / total_recals) * 100 AS failure_rate
FROM recalibration_status
ORDER BY failure_rate DESC;
```

---

## **Related Patterns**
1. **[Dynamic Sampling](https://docs.example.com/dynamic-sampling)**
   - *Use Case*: Adjust sampling rates in `profiles.schema` based on data volume changes.
   - *Integration*: Trigger recalibration when sampling thresholds cross predefined bounds (e.g., < 0.001 or > 0.5).

2. **[Metadata Store](https://docs.example.com/metadata-store)**
   - *Use Case*: Store profile attributes in a graph database for lineage analysis.
   - *Integration*: Link `profile_attributes` to related entities (e.g., data sources, transformations).

3. **[Data Quality Rules](https://docs.example.com/data-quality-rules)**
   - *Use Case*: Extend validation rules in `profile_attributes` to flag outliers.
   - *Integration*: Use `valid_from` timestamps to apply rules to specific data slices.

4. **[Event-Driven Architecture](https://docs.example.com/event-driven)**
   - *Use Case*: Trigger recalibration on schema changes (e.g., column additions).
   - *Integration*: Subscribe to database event logs (e.g., Debezium) to update `last_updated` in `profiles.schema`.

5. **[Incremental Profiling](https://docs.example.com/incremental-profiling)**
   - *Use Case*: Recompute attributes for new data without reprofiling the entire table.
   - *Integration*: Partition `profile_attributes` by time and reprofile only new partitions.

---

## **Best Practices**
1. **Automate Recalibration**:
   - Schedule jobs (e.g., Airflow) to update baselines quarterly for stable datasets, monthly for volatile ones.
   - Example DAG:
     ```python
     @task
     def run_recalibration(profile_id: str):
         update_sql = f"""
         UPDATE profile_attributes
         SET baseline_value = current_value,
             current_value = (SELECT ... FROM new_data_samples...)
         WHERE profile_id = '{profile_id}'
         """
         execute_sql(update_sql)
     ```

2. **Tolerate Drift**:
   - Set configurable thresholds (e.g., 10% drift triggers a warning, 20% triggers auto-fix).
   - Example logic:
     ```python
     if abs(current - baseline) > threshold:
         if drift_type == "increase_nulls":
             log_warning(f"Column {column_name} null rate spiked")
         else:
             adjust_rule(column_name, new_threshold)
     ```

3. **Document Changes**:
   - Use `recalibration_logs.error_message` to explain fixes (e.g., "Adjusted null threshold from 5% to 8% due to schema update").
   - Link logs to tickets (e.g., Jira) for traceability.

4. **Isolate Testing**:
   - Run recalibration in a staging environment first to validate rules against production-like data.

5. **Optimize Performance**:
   - Cache profile attributes (e.g., Redis) for read-heavy workflows.
   - Parallelize recalibration across columns using a task queue (e.g., Celery).

---
**Note**: Adjust schema columns (e.g., precision of `sampling_rate`) based on your data scale and tooling (e.g., Snowflake vs. PostgreSQL).