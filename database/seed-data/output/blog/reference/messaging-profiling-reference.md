**[Pattern] Messaging Profiling Reference Guide**
*Version 1.0 | Last Updated: [Insert Date]*
---
### **1. Overview**
**Messaging Profiling** is a pattern used to categorize, segment, and analyze message flows within a distributed system by applying behavioral attributes (e.g., message frequency, latency, payload size, or routing behavior). This pattern enables observability, performance tuning, and targeted enforcement of SLAs or rate limits. Profiling helps distinguish between "normal" and anomalous traffic, supports auto-scaling decisions, and enables targeted logging/alerting.

Key use cases:
- Detecting and mitigating API abuse or DoS attacks.
- Optimizing resource allocation based on message volume patterns.
- Enabling predictive scaling for bursty workloads.
- Segmenting support for different message types (e.g., async tasks vs. real-time events).

---

### **2. Schema Reference**
Below are the core entities and attributes used in messaging profiling. The schema assumes a data-driven approach (e.g., storing profiles in a time-series database or message metadata).

| **Entity**               | **Field**                | **Description**                                                                 | **Data Type**       | **Example**                          |
|--------------------------|--------------------------|---------------------------------------------------------------------------------|----------------------|---------------------------------------|
| **Profile**              | `profile_id`             | Unique identifier for the profile (e.g., `profile_v1_auth_token`).              | UUID/String          | `abc123-xyz789`                       |
|                          | `name`                   | Human-readable description (e.g., `auth-service-heavy`).                          | String               | `"API-auth-90qps"`                   |
|                          | `created_at`             | Creation timestamp.                                                                | Timestamp            | `2024-05-15T08:00:00Z`               |
|                          | `updated_at`             | Last modification timestamp.                                                     | Timestamp            | `2024-05-16T14:30:00Z`               |
|                          | `status`                 | Lifecycle stage (`active`, `deprecated`, `archived`).                           | Enum                 | `"active"`                            |
| **Metrics**              | `message_volume`         | Average/burst messages per second (`avg`, `max`, `p99`).                         | Numeric (rate)       | `{avg: 50, max: 1200, p99: 800}`     |
|                          | `latency_distribution`   | Percentiles of processing time (e.g., `p50`, `p90`, `p99`).                     | Numeric (ms)         | `{p50: 100, p90: 250, p99: 1500}`    |
|                          | `payload_size_avg`       | Average payload size in bytes.                                                   | Numeric (bytes)      | `1200`                                 |
|                          | `routing_path`           | Path taken by messages (e.g., `queueA → serviceB → topicC`).                    | String/Array         | `["queue/orders", "service/payment"]`|
|                          | `source_destination`     | Source/target systems (e.g., `client_app:payment_service`).                     | String               | `"webapp:checkout"`                  |
| **Rules**                | `rate_limit`             | Max allowed messages/second (e.g., `{profile_id: "abc123", limit: 300}`).      | Numeric/Object       | `300` (or `{profile_id: "abc123", limit: 300})` |
|                          | `priority`               | Placement in queue/priority queue (e.g., `low`, `high`, `critical`).            | Enum                 | `"high"`                              |
|                          | `sla_violation_action`   | Action on SLA breach (e.g., `drop`, `throttle`, `notify`).                       | Enum                 | `"throttle"`                          |
| **Annotations**          | `tags`                   | Custom labels (e.g., `env:prod`, `team:finance`).                               | Array                | `["env=prod", "team=finance"]`       |
|                          | `description`            | Free-text notes (e.g., "Spike during Black Friday").                            | String               | `"High-volume during Q4 sales."`     |

---
**Relationships:**
- A `Profile` may have **multiple `Metrics`** (time-series data).
- A `Profile` can enforce **one or more `Rules`**.
- `Annotations` are appended to `Profiles` for categorization.

---

### **3. Implementation Details**
#### **3.1. Profiling Workflow**
1. **Capture Metadata**:
   - Instrument message brokers (e.g., Kafka, RabbitMQ) or APIs to log:
     - Message headers (e.g., `X-Profile-ID`, `X-Source`).
     - Timestamps (`timestamp`, `processing_time`).
     - Payload size (`Content-Length`).
   - Use middleware (e.g., Envoy, Istio) to capture routing paths.

2. **Aggregate Data**:
   - Use a time-series DB (e.g., Prometheus, InfluxDB) or a message-aware store (e.g., Elasticsearch) to store metrics.
   - Example query (Pseudocode):
     ```sql
     INSERT INTO profiles_metrics (profile_id, message_volume_avg, timestamp)
     VALUES ('abc123', 50, NOW());
     ```

3. **Apply Rules**:
   - Evaluate metrics against `Rules` at runtime (e.g., in an API gateway or service mesh).
   - Example: If `message_volume_max > 1000` for `profile_id: "abc123"`, trigger `sla_violation_action: "throttle"`.

4. **Update Profiles**:
   - Recalculate profiles daily/on-demand using rolling windows (e.g., 7-day averages).
   - Mark deprecated profiles with `status: "archived"`.

#### **3.2. Tools & Libraries**
| **Component**       | **Options**                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| **Messaging Broker** | Kafka (with `kafka-metrics-reporter`), RabbitMQ (with `rabbitmq-prometheus`).|
| **Observability**    | Prometheus, Datadog, OpenTelemetry.                                          |
| **Storage**          | InfluxDB, TimescaleDB, Elasticsearch.                                       |
| **Runtime Enforcement** | Envoy, Kong, AWS WAF, Azure API Management.                                |

#### **3.3. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│   Client    │───▶│  API Gateway│───▶│   Service   │───▶│   Message Broker│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────────┘
                                   │                             │
                                   ▼                             ▼
                      ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐
                      │        Profiling DB      │    │       Metrics Collector   │
                      │ (InfluxDB/Elasticsearch) │    │ (Prometheus/OpenTelemetry)│
                      └──────────────────────────┘    └──────────────────────────┘
                                      ▲
                                      │
                      ┌─────────────▼─────────────┐
                      │        Decision Engine    │ (Evaluates rules)
                      └──────────────────────────┘
```

---

### **4. Query Examples**
#### **4.1. Querying Profile Metrics (SQL-like Pseudocode)**
```sql
-- Get avg message volume for a profile over the last 24h
SELECT
  profile_id,
  AVG(message_volume_avg) as avg_volume,
  MAX(message_volume_max) as peak_volume
FROM profiles_metrics
WHERE profile_id = 'abc123'
  AND timestamp > NOW() - INTERVAL '24h'
GROUP BY profile_id;

-- Find profiles exceeding a rate limit
SELECT p.*
FROM profiles p
JOIN rules r ON p.profile_id = r.profile_id
WHERE r.rate_limit < (
  SELECT AVG(message_volume_max)
  FROM profiles_metrics
  WHERE profiles_metrics.profile_id = p.profile_id
  AND timestamp > NOW() - INTERVAL '1h'
);
```

#### **4.2. Querying in OpenTelemetry (PromQL)**
```promql
# alert if a profile's p99 latency spikes
rate(profile_latency{p99="true", profile_id="abc123"}[5m]) > 1000
```

#### **4.3. Kafka Metrics (CLI)**
```bash
# Get topic-level metrics (via kafka-consumer-groups or Prometheus)
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group abc123
# Output: Lag, messages/sec, etc.
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use Together**                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **Circuit Breaker**       | Temporarily stops forwarding requests to avoid overload.                        | Combine with profiling to detect cascading failures. |
| **Rate Limiting**         | Controls message/connection rates to prevent abuse.                            | Use profiling to dynamically adjust limits.      |
| **Observability Pipeline**| Collects, stores, and visualizes telemetry data.                               | Profiling feeds into observability for insights.   |
| **Service Mesh**          | Manages inter-service communication (e.g., Envoy, Istio).                     | Mesh supports routing and instrumentation.        |
| **Request/Response**      | Traditional synchronous pattern.                                               | Profile API calls vs. async messages.              |
| **Event Sourcing**        | Stores state changes as a sequence of events.                                 | Profile event volume for replay/retries.          |

---

### **6. Best Practices**
1. **Granularity**:
   - Start with coarse profiles (e.g., by service) and refine (e.g., by endpoint).
2. **Monitoring**:
   - Alert on profile drift (e.g., `message_volume` deviates >20% from baseline).
3. **Cost Optimization**:
   - Profile only critical paths; avoid overhead on low-volume queues.
4. **Security**:
   - Store sensitive metadata (e.g., `source_ip`) in encrypted fields.
5. **Testing**:
   - Simulate traffic spikes to validate rule enforcement (e.g., using Locust).

---
**Example Alert Rule (Prometheus):**
```yaml
- alert: ProfileVolumeSpike
  expr: increase(profile_metrics{profile_id="abc123"}[5m]) > 1000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Profile 'abc123' exceeded 1000 msg/5m"
```