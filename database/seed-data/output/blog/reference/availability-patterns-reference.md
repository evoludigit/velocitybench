---

# **[Availability Patterns] Reference Guide**

---

## **Overview**
The **Availability Patterns** define standardized ways to track, control, and query application service statuses, outages, and scheduled maintenance events. These patterns ensure consistent communication and transparency between services, teams, and users about system availability.

Patterns include:
- **Status Messages**: Structured announcements for incidents or maintenance.
- **SLA Metrics**: Service Level Agreement reporting (e.g., uptime/downtime percentages).
- **Availability Scheduling**: Predefined maintenance windows and emergency overrides.
- **Dependency Tracking**: How failures in one service ripple through dependent systems.

Use cases include:
- **Incident Management**: Real-time alerts for outages.
- **Capacity Planning**: Predictive scheduling for upgrades.
- **User Communication**: Clear notifications to stakeholders.

---

## **Key Concepts**
### **1. Status Types**
Define availability states with standardized labels:

| **Code** | **Name**            | **Description**                                                                 |
|----------|---------------------|---------------------------------------------------------------------------------|
| `UP`     | Operational         | Service running as expected.                                                   |
| `DEGRADED` | Partial Outage     | Service functional but with reduced performance or limited features.           |
| `DOWN`   | Full Outage         | Service unavailable; all features impacted.                                      |
| `MAINTENANCE` | Scheduled Downtime | Planned outage for updates or upgrades.                                         |
| `UNKNOWN` | Unclassified        | System status unclear due to monitoring gaps or errors.                         |
| `WARNING` | Pre-Outage Alert    | Indicates an impending failure (e.g., high latency, resource exhaustion).       |

---

### **2. Schema Reference**
Define schemas for structured data interchange.

#### **Status Message Schema**
```json
{
  "id": "string (UUID)",
  "type": ["status_update", "maintenance_schedule", "sla_metric_update"],
  "timestamp": "ISO 8601 timestamp",
  "affected_services": ["service1", "service2"],
  "status": ["UP", "DEGRADED", "DOWN", ...],
  "message": "string (detailed explanation)",
  "impact": {
    "users": "integer (affected user count)",
    "features": ["list of unavailable features"],
    "estimates": {
      "start": "ISO 8601",
      "end": "ISO 8601",
      "resolution": "ISO 8601"
    }
  },
  "categories": ["incident", "outage", "feature_change", ...],
  "resolved": "boolean (default: false)",
  "references": ["ticket_link", "blog_post"]
}
```

#### **SLA Metric Schema**
```json
{
  "service": "string (service name)",
  "metric_period": "string (e.g., '2023-01-01T00:00:00Z/2023-01-31T23:59:59Z')",
  "uptime_percentage": "float (0.0–100.0)",
  "degradation_minutes": "integer",
  "sla_threshold": "float (e.g., 99.9%)",
  "actual_vs_target": {
    "met": "boolean",
    "penalties": "string (e.g., 'no penalty', '5% revenue deduction')"
  }
}
```

#### **Maintenance Schedule Schema**
```json
{
  "schedule_id": "string (UUID)",
  "service": "string (service name)",
  "window": [
    {
      "start": "ISO 8601",
      "end": "ISO 8601",
      "timezone": "string"
    }
  ],
  "recurrence": "string (e.g., 'weekly:Mon-Fri 22:00-02:00')",
  "status": ["CANCELED", "POSTPONED", "SCHEDULED", "IN_PROGRESS"],
  "categories": ["security_update", "infrastructure_upgrade", ...],
  "notes": "string (technical or user-facing details)"
}
```

---

## **Implementation Details**

### **1. Data Flow**
- **Events**: Status changes trigger events published to a streaming platform (e.g., Apache Kafka, AWS Kinesis).
- **Storage**: Write records to a time-series database (e.g., InfluxDB) and a document store (e.g., MongoDB) for long-term history.
- **Retrieval**: Query via REST/GraphQL APIs or direct DB access.

### **2. Communication Channels**
| **Channel**       | **Format**                     | **Audience**                  |
|-------------------|--------------------------------|-------------------------------|
| **Incident Page** | Web dashboard + RSS/JSON API   | Users, Developers             |
| **Email Alerts**  | Structured email templates      | On-call teams, Subscribers    |
| **SMS/Slack**     | Short-form summaries           | Emergency notifications       |
| **API Updates**   | Real-time WebSocket pushes     | Monitoring tools (Prometheus) |

### **3. Example Workflow**
1. **Outage Detection**: A monitoring system detects a `DOWN` status for `service:auth`.
2. **Event Pub/Sub**: The event is sent to a Kafka topic (`status-updates`).
3. **Processing**: A Lambda function validates the event and updates MongoDB.
4. **Notification**: Slack messages and emails are triggered for the `security` team.
5. **Dashboard Update**: The incident appears on the public status page.

---

## **Query Examples**

### **1. Get Current Status of a Service**
```sql
-- SQL (MongoDB)
db.status_messages.find({
  "affected_services": "auth-service",
  "timestamp": { $gte: ISODate("2023-10-01") },
  "status": { $nin: ["RESOLVED"] }
}).sort({ "timestamp": -1 }).limit(1);
```

**Response**:
```json
{
  "id": "5f8d8c7b7e6a1f2b3c4d5e6f",
  "status": "DOWN",
  "affected_services": ["auth-service"],
  "impact": {
    "users": 1500,
    "features": ["login", "password_reset"],
    "estimates": {
      "start": "2023-10-05T14:30:00Z",
      "resolution": "2023-10-05T15:15:00Z"
    }
  }
}
```

---

### **2. Check SLA Compliance for Q3 2023**
```graphql
query SLAMetrics {
  slaMetrics(
    service: "payment-service",
    period: "2023-07-01/2023-09-30"
  ) {
    uptimePercentage
    degradationMinutes
    actualVsTarget {
      met
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "slaMetrics": {
      "uptimePercentage": 99.7,
      "degradationMinutes": 180,
      "actualVsTarget": {
        "met": false
      }
    }
  }
}
```

---

### **3. List Upcoming Maintenance Windows**
```bash
# REST API example
curl -X GET "https://api.example.com/v1/maintenance" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: application/json" \
  | jq '.schedules[] | select(.status == "SCHEDULED" and .service == "storage")'
```

**Response**:
```json
[
  {
    "schedule_id": "a1b2c3d4-5678...",
    "service": "storage",
    "window": [
      {
        "start": "2023-10-15 02:00:00+00:00",
        "end": "2023-10-15 05:00:00+00:00"
      }
    ],
    "categories": ["infrastructure_upgrade"]
  }
]
```

---

## **Related Patterns**
1. **[Circuit Breaker Pattern]**
   - *Purpose*: Prevent cascading failures. Use with `Availability Patterns` to correlate outages with service degradation in dependent systems.
   - *Sync*: Monitor `DOWN` statuses to trigger circuit breakers in client applications.

2. **[Feature Flags Pattern]**
   - *Purpose*: Gradually roll out new features or hide degraded functionality.
   - *Sync*: Update feature flags when `STATUS=DEGRADED` to disable affected features.

3. **[Canary Releases Pattern]**
   - *Purpose*: Test updates in a subset of users.
   - *Sync*: Use `MAINTENANCE` status to notify users during canary periods.

4. **[Observability Patterns]**
   - *Purpose*: Gather metrics, logs, and traces for troubleshooting.
   - *Sync*: Correlate `status` events with metrics (e.g., `latency > 1000ms`) for root cause analysis.

5. **[Alerting Patterns]**
   - *Purpose*: Automate notifications for critical status changes.
   - *Sync*: Trigger alerts when `status` transitions from `UP` to `DOWN` or `DEGRADED`.

6. **[Time-Series Database Patterns]**
   - *Purpose*: Store and query availability metrics over time.
   - *Sync*: Ingest `status` and `sla_metric` data into InfluxDB/TSDB for trend analysis.

---

## **Best Practices**
- **Standardize Terminology**: Use the same `status` codes across all services.
- **Automate Status Updates**: Integrate with CI/CD pipelines to auto-update during deployments.
- **Document Impact**: Include clear `impact` fields to help users plan workarounds.
- **Audit Logs**: Log all status changes for compliance and post-mortems.
- **User Communication**: Provide multi-channel updates with urgency levels (e.g., `WARNING` vs. `DOWN`).

---
**Last Updated**: October 2023
**Owner**: Platform Reliability Team