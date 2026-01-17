# **[Pattern] Analytics Tracking Patterns – Reference Guide**

---

## **Overview**
The **Analytics Tracking Patterns** ensure consistent, scalable, and actionable data collection for business intelligence, user behavior analysis, and performance monitoring. This pattern defines reusable tracking structures—including event schemas, categorization, and implementation strategies—to reduce redundancy, improve maintainability, and enhance cross-team collaboration. Whether tracking user interactions, business metrics, or system events, these patterns standardize how data is captured, processed, and analyzed, enabling better decision-making.

---

## **Schema Reference**
The following table outlines core components of a *standardized analytics tracking event*. Adjust fields based on your use case (e.g., marketing, product analytics, or financial tracking).

| **Field**               | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `event_id`               | UUID           | Unique identifier for the event (auto-generated).                                                 | `"550e8400-e29b-41d4-a716-446655440000"`                                         |
| `event_type`             | String (enum)  | Category of event (e.g., `user_action`, `system_performance`, `business_metric`).                   | `"user_action"`, `"purchase_conversion"`                                          |
| `event_name`             | String         | Specific action/occurrence name.                                                                        | `"product_view"`, `"checkout_start"`                                                |
| `event_timestamp`        | ISO 8601       | When the event occurred (server-side timestamp).                                                     | `"2024-05-20T14:30:00Z"`                                                          |
| `user_id`                | String         | Unique user identifier (e.g., session hash or DB ID).                                              | `"usr_12345"`                                                                     |
| `session_id`             | String         | Unique session identifier for context.                                                             | `"sess_67890"`                                                                     |
| `properties` (obj)       | JSON           | Key-value pairs for granular details (e.g., `product_id`, `referrer`).                             | `{ "product_id": "1001", "referrer": "google.com" }`                               |
| `context` (obj)          | JSON           | Additional metadata (e.g., device, location, app version).                                         | `{ "device": "mobile", "os": "iOS", "country": "US" }`                            |
| `session_properties` (obj)| JSON           | Persistent session-level data (e.g., user role, plan tier).                                        | `{ "user_role": "premium", "plan_tier": "pro" }`                                  |
| `metadata` (obj)         | JSON           | Legacy/compatibility fields (avoid unless necessary).                                               | `{ "legacy_source": "api_v1" }`                                                  |
| `is_primary`             | Boolean        | Flags critical events for priority processing (e.g., `true` for purchases).                        | `true`/`false`                                                                   |

---

### **Key Patterns for Event Categorization**
1. **User Behavior Events**
   - Track interactions like:
     - `product_view`, `add_to_cart`, `checkout_progress`, `purchase_completion`.
   - **Schema Example**:
     ```json
     {
       "event_type": "user_action",
       "event_name": "purchase_completion",
       "properties": {
         "order_id": "ORD_20240520_12345",
         "total_amount": 99.99,
         "payment_method": "credit_card"
       }
     }
     ```

2. **System/Performance Events**
   - Monitor infrastructure or API usage:
     - `server_error`, `api_latency`, `database_query`.
   - **Schema Example**:
     ```json
     {
       "event_type": "system_performance",
       "event_name": "api_latency",
       "properties": {
         "endpoint": "/api/v1/users",
         "response_time_ms": 850,
         "status_code": 200
       }
     }
     ```

3. **Business Metrics**
   - Aggregate KPIs (e.g., `revenue`, `user_churn`).
   - **Schema Example**:
     ```json
     {
       "event_type": "business_metric",
       "event_name": "revenue_by_region",
       "properties": {
         "region": "europe",
         "amount": 50000.00,
         "currency": "EUR"
       }
     }
     ```

---

## **Implementation Details**
### **1. Data Collection Layers**
| **Layer**          | **Responsibility**                                                                 | **Tools/Examples**                                                                 |
|--------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Frontend**       | Capture user interactions (e.g., clicks, form submissions).                       | JavaScript SDKs (Google Analytics, Amplitude, Segment).                           |
| **Backend**        | Validate/enrich events before forwarding (e.g., add `session_id`).                | Custom APIs, middleware (Express.js, Django).                                   |
| **Pipeline**       | Route, transform, and store events (e.g., Kafka, AWS Kinesis).                   | Event streaming platforms, batch processors.                                     |
| **Storage**        | Persist events for analysis (e.g., time-series DBs, warehouses).                  | Snowflake, BigQuery, Elasticsearch.                                              |
| **Analysis**       | Query and visualize data (e.g., dashboards, ML models).                          | Looker, Tableau, custom SQL queries.                                             |

### **2. Best Practices**
- **Consistency**: Use standardized `event_name` values across teams.
- **Minimalism**: Avoid bloating `properties`—group related fields (e.g., `product` object).
- **Privacy**: Anonymize PII (e.g., `user_id` = hashed session token).
- **Sampling**: For high-volume events, implement probabilistic sampling (e.g., 1% of `product_view` events).
- **Validation**: Enforce schemas (e.g., using JSON Schema or OpenAPI specs).

---

## **Query Examples**
### **1. User Behavior Analysis**
**Question**: *"What’s the conversion rate from `add_to_cart` to `purchase_completion`?"*
**SQL (BigQuery)**:
```sql
SELECT
  `properties.add_to_cart.user_id` AS user_id,
  COUNTIF(`event_name` = 'purchase_completion') / COUNT(*) AS conversion_rate
FROM `analytics_events`
WHERE `event_name` = 'add_to_cart'
GROUP BY user_id;
```

### **2. Performance Alerting**
**Question**: *"Notify if API latency exceeds 1s for `/api/v1/users`."*
**ELT Pipeline (Pseudo-Code)**:
```python
# Pseudocode for Kafka consumer (Python)
from confluent_kafka import Consumer

consumer = Consumer({"bootstrap.servers": "kafka:9092"})
consumer.subscribe(["analytics_events"])

for msg in consumer:
    event = msg.value()
    if (event["event_name"] == "api_latency" and
        event["properties"]["endpoint"] == "/api/v1/users" and
        event["properties"]["response_time_ms"] > 1000):
        send_slack_alert(f"Latency spike: {event['properties']['response_time_ms']}ms")
```

### **3. Business KPI Tracking**
**Question**: *"Calculate weekly revenue by region."*
**Presto SQL**:
```sql
SELECT
  DATE_TRUNC('week', `event_timestamp`) AS week,
  `properties.region`,
  SUM(CAST(`properties.amount` AS DECIMAL(10,2))) AS revenue
FROM analytics.events
WHERE `event_name` = 'revenue_by_region'
GROUP BY 1, 2
ORDER BY 1, 2;
```

---

## **Related Patterns**
1. **[Event-Driven Architecture](https://patterns.dev/event-driven-architecture)**
   - Aligns with pipeline layer in Analytics Tracking Patterns for real-time processing.

2. **[Data Warehouse Schema Design](https://patterns.dev/star-schema)**
   - Use a star schema for `event_type` (fact table) + `properties` (dimensions) to optimize queries.

3. **[Feature Flags](https://patterns.dev/feature-flags)**
   - Test tracking changes (e.g., A/B experiments) without deploying new event schemas.

4. **[Rate Limiting](https://patterns.dev/rate-limiting)**
   - Apply to high-volume events (e.g., `page_view`) to avoid pipeline overload.

5. **[Data Lineage](https://patterns.dev/data-lineage)**
   - Track how events flow from collection to analysis for auditability.

---
**Note**: Combine with **[Observability Patterns](https://patterns.dev/observability)** for correlating tracking data with logs/metrics.