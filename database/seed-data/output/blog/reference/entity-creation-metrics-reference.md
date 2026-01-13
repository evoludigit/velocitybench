# **[Pattern] Entity Creation Metrics Reference Guide**

---

## **1. Overview**
The **Entity Creation Metrics** pattern provides a structured approach to tracking, analyzing, and optimizing the creation of new entities (e.g., users, products, orders, or system resources) within a platform or application. This pattern is essential for understanding adoption trends, identifying bottlenecks in onboarding/creation workflows, and improving efficiency.

Key use cases include:
- **Growth monitoring** – Tracking how quickly new entities (e.g., subscribers, accounts) are being created.
- **Performance tuning** – Identifying inefficiencies in entity creation processes (e.g., API latency, backend delays).
- **Anomaly detection** – Spotting spikes, dips, or unusual patterns in entity creation rates.
- **Cost optimization** – Measuring resource allocation (e.g., compute, storage) during entity generation.

This pattern assumes a logging-based or event-driven architecture, where entity creation events are captured, enriched, and analyzed in real time or near real time.

---

## **2. Schema Reference**
Below are the core schema components required for this pattern.

| **Component**         | **Description**                                                                                     | **Data Type**          | **Example Values**                                                                 | **Required** |
|-----------------------|-----------------------------------------------------------------------------------------------------|------------------------|-----------------------------------------------------------------------------------|--------------|
| **Event ID**          | Unique identifier for the entity creation event (e.g., UUID).                                         | `string`               | `"e17a4c8f-3e2d-4f7a-9b8c-1d2e3f4a5b6c"`                                         | ✅ Yes        |
| **Entity Type**       | The category of entity being created (e.g., `user`, `product`, `order`, `invoice`).                 | `string`               | `"user"`, `"product_v2"`                                                            | ✅ Yes        |
| **Entity ID**         | The generated ID of the newly created entity (e.g., database primary key or internal ID).           | `string`               | `"usr_456789"`, `"prod_12345"`                                                     | ✅ Yes        |
| **Creation Timestamp**| When the entity was created (ISO 8601 format).                                                      | `timestamp`            | `"2024-05-20T14:30:00Z"`                                                        | ✅ Yes        |
| **Source System**     | The origin of the creation request (e.g., `frontend_app`, `mobile_app_v3`, `admin_panel`).          | `string`               | `"mobile_app_v3"`, `"api_gateway"`                                                 | ❌ Optional   |
| **User ID**           | The user (if applicable) who initiated the creation (e.g., customer ID, admin ID).                    | `string`               | `"usr_12345"`, `null`                                                            | ❌ Optional   |
| **Metadata**          | Key-value pairs for additional context (e.g., `success`=`true/false`, `error_code`, `region`).       | `object`               | `{ "success": true, "region": "us-west-2" }`                                      | ❌ Optional   |
| **Duration (ms)**     | Time taken to process the creation request (end-to-end latency).                                    | `integer`              | `420` (milliseconds)                                                              | ❌ Optional   |
| **API Endpoint**      | The exact API endpoint or service invoked (e.g., `/v1/users/create`, `/inventory/add`).              | `string`               | `"/v1/users/create"`                                                              | ❌ Optional   |
| **Tags**              | Custom labels for filtering (e.g., `campaign_id`, `feature_flag`).                                   | `array<string>`        | `["summer_sale", "beta_feature"]`                                                | ❌ Optional   |

---
**Example JSON Payload:**
```json
{
  "event_id": "e17a4c8f-3e2d-4f7a-9b8c-1d2e3f4a5b6c",
  "entity_type": "user",
  "entity_id": "usr_456789",
  "creation_timestamp": "2024-05-20T14:30:00Z",
  "source_system": "mobile_app_v3",
  "user_id": "usr_12345",
  "metadata": {
    "success": true,
    "region": "us-west-2"
  },
  "duration_ms": 890,
  "api_endpoint": "/v1/users/create",
  "tags": ["referral_code_XYZ"]
}
```

---

## **3. Query Examples**
### **3.1 Basic Aggregations**
**Query:** *Count daily new users by source system.*
```sql
SELECT
  DATE(creation_timestamp) AS day,
  source_system,
  COUNT(*) AS new_users
FROM entity_creation_events
WHERE entity_type = 'user'
GROUP BY day, source_system
ORDER BY day, new_users DESC;
```

**Query:** *Calculate average duration for entity creation by API endpoint.*
```sql
SELECT
  api_endpoint,
  AVG(duration_ms) AS avg_duration_ms
FROM entity_creation_events
WHERE success = true
GROUP BY api_endpoint
ORDER BY avg_duration_ms DESC;
```

---

### **3.2 Time-Series Analysis**
**Query:** *Line chart of hourly entity creation rate (7-day window).*
```sql
SELECT
  HOUR(creation_timestamp) AS hour_of_day,
  COUNT(*) AS entities_created
FROM entity_creation_events
WHERE creation_timestamp >= NOW() - INTERVAL '7 days'
  AND entity_type = 'order'
GROUP BY hour_of_day
ORDER BY hour_of_day;
```

**Query:** *Week-over-week growth comparison for a specific entity type.*
```sql
WITH weekly_counts AS (
  SELECT
    DATE_TRUNC('week', creation_timestamp) AS week_start,
    entity_type,
    COUNT(*) AS count
  FROM entity_creation_events
  WHERE entity_type IN ('user', 'product')
  GROUP BY week_start, entity_type
)
SELECT
  week_start,
  entity_type,
  count,
  LAG(count, 1) OVER (PARTITION BY entity_type ORDER BY week_start) AS prev_week_count,
  count - LAG(count, 1) OVER (PARTITION BY entity_type ORDER BY week_start) AS delta
FROM weekly_counts
ORDER BY entity_type, week_start;
```

---

### **3.3 Anomaly Detection**
**Query:** *Identify unusual spikes in creation events (using Z-score).*
```sql
WITH hourly_stats AS (
  SELECT
    HOUR(creation_timestamp) AS hour,
    AVG(COUNT(*)) AS avg_count,
    STDDEV(COUNT(*)) AS stddev_count
  FROM entity_creation_events
  GROUP BY HOUR(creation_timestamp)
)
SELECT
  e.hour,
  COUNT(*) AS actual_count,
  s.avg_count,
  (COUNT(*) - s.avg_count) / NULLIF(s.stddev_count, 0) AS z_score
FROM entity_creation_events e
CROSS JOIN hourly_stats s
WHERE HOUR(e.creation_timestamp) = s.hour
GROUP BY e.hour, s.avg_count, s.stddev_count
HAVING ABS(z_score) > 3  -- Threshold for anomaly
ORDER BY z_score DESC;
```

---

### **3.4 User-Specific Metrics**
**Query:** *Track creation success rate per user (e.g., admins vs. regular users).*
```sql
SELECT
  user_id,
  COUNT(*) AS total_attempts,
  SUM(CASE WHEN metadata->>'success' = 'true' THEN 1 ELSE 0 END) AS successful,
  (SUM(CASE WHEN metadata->>'success' = 'true' THEN 1 ELSE 0 END) * 100.0 /
   COUNT(*)) AS success_rate
FROM entity_creation_events
GROUP BY user_id
ORDER BY success_rate DESC;
```

---

## **4. Implementation Details**
### **4.1 Key Concepts**
1. **Event Logging:**
   - Entity creation events should be logged **asynchronously** to avoid blocking the main workflow.
   - Use a reliable event pipeline (e.g., Kafka, Pub/Sub, or a logging service like ELK/CloudWatch).

2. **Enrichment:**
   - Append contextual data (e.g., geographic location, campaign ID, device info) to events for deeper analysis.
   - Example enrichment fields:
     ```json
     "enriched_data": {
       "device_type": "mobile",
       "os_version": "iOS 17.4",
       "country": "US"
     }
     ```

3. **Sampling (for High-Volume Systems):**
   - If creation rates exceed 10K events/sec, implement **statistical sampling** (e.g., 1% sampling) to balance accuracy and cost.

4. **Storage:**
   - **Hot Data (last 7 days):** High-frequency, real-time analysis (e.g., time-series DB like InfluxDB).
   - **Cold Data (older):** Aggregate metrics (e.g., BigQuery, Snowflake) for long-term trends.

5. **Alerting:**
   - Set up alerts for:
     - Sudden drops in creation rates (potential outages).
     - Latency spikes (>95th percentile threshold).
     - Error rates exceeding 1% for critical entity types.

---

### **4.2 Example Architecture**
```
[Application] → (Async) → [Event Producer] → [Event Pipeline (Kafka)]
        ↓
[Enrichment Layer] → [Time-Series DB (InfluxDB)] ← [Dashboard (Grafana)]
        ↓
[Aggregation Layer] → [Data Warehouse (BigQuery)]
```

---

### **4.3 Tools & Libraries**
| **Category**          | **Tools/Libraries**                                                                 |
|-----------------------|------------------------------------------------------------------------------------|
| **Event Logging**     | OpenTelemetry, ELK Stack, Cloud Logging (GCP/AWS)                                   |
| **Processing**        | Apache Flink, Spark Streaming, AWS Lambda (event-driven)                          |
| **Storage**           | InfluxDB (time-series), BigQuery (analytics), PostgreSQL (hybrid)                  |
| **Visualization**     | Grafana, Metabase, Tableau                                                           |
| **Alerting**          | PagerDuty, Opsgenie, Datadog                                                           |

---

## **5. Related Patterns**
1. **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)**
   - Use event sourcing to **persist entity state changes** for replayability and auditing alongside metrics.

2. **[Rate Limiting & Throttling](https://en.wikipedia.org/wiki/Rate_limiting)**
   - Complement this pattern with rate-limiting rules to prevent abuse during high-volume creation events.

3. **[A/B Testing for Onboarding](https://www.split.io/ab-testing)**
   - Measure how different onboarding flows impact entity creation success rates.

4. **[Cost Monitoring for Entity Generation](https://cloud.google.com/blog/products/architecture)**
   - Track cloud resource usage (e.g., compute, storage) tied to entity creation to optimize costs.

5. **[Entity Lifecycle Metrics](https://www.martinfowler.com/eaaCatalog/lifecycle.html)**
   - Extend this pattern to include **deletion/updates** for end-to-end entity activity tracking.

---

## **6. Best Practices**
- **Granularity:** Log at the **entity-type level** (e.g., `user`, `product`) rather than generic "creation" events.
- **Consistency:** Use a **standardized schema** (e.g., Avro, Protobuf) for schema evolution.
- **Retention:** Archive cold data to reduce costs while keeping recent data for analysis.
- **Privacy:** Anonymize PII (Personally Identifiable Information) in logs unless compliance requires retention.
- **Performance:** Avoid blocking the main thread during event logging; use fire-and-forget patterns.

---
**See also:**
- [Google Cloud’s Eventarc](https://cloud.google.com/eventarc) for serverless event routing.
- [OpenTelemetry Metrics](https://opentelemetry.io/docs/specs/otel/metrics/) for standardized instrumentation.