# **[Pattern] Availability Guidelines Reference Guide**

---

## **Overview**
The **Availability Guidelines** pattern defines standardized rules for managing service availability, ensuring predictable uptime and graceful degradation during disruptions. This pattern helps teams communicate expected availability levels, define maintenance windows, and establish failure recovery processes. It applies to microservices, APIs, and distributed systems, aligning technical implementations with business and operational goals.

Key use cases include:
- **APIs**: Documenting expected response times, error handling, and retry policies.
- **Microservices**: Defining degradation thresholds and fallback mechanisms.
- **Infrastructure**: Outlining disaster recovery procedures and backup schedules.
- **Compliance**: Meeting SLAs (Service Level Agreements) and regulatory requirements.

This guide provides a structured approach to implementing and documenting availability guidelines, ensuring consistency across services.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **Availability Window** | Scheduled time periods where services may undergo maintenance or deprecation.                     |
| **SLO (Service Level Objective)** | Quantitative target for service availability (e.g., "99.9% uptime").                              |
| **Graceful Degradation** | Non-critical functionality is disabled during outages to preserve core service availability.     |
| **Retention Policy**    | How long error logs, metrics, or failed requests are stored for troubleshooting.                   |
| **Recovery Time Objective (RTO)** | Maximum acceptable time to restore service after a failure.                                        |
| **Recovery Point Objective (RPO)** | Maximum acceptable data loss during a failure (e.g., last 5 minutes of transactions).              |

---

## **Schema Reference**

Below is the structured schema for defining availability guidelines in configuration files (e.g., YAML, JSON) or code annotations.

### **1. Service Availability Declaration**
```yaml
availability:
  name: "User Authentication Service"
  version: "v1.0.0"
  slo:
    target: 99.95%  # Target availability (e.g., 99.9% = 43.8 mins downtime/year)
    measurement_window: "24 hours"  # Window for SLO calculation
  maintenance:
    windows:
      - start: "2024-01-01T02:00:00Z"  # UTC
        end:   "2024-01-01T04:00:00Z"
        timezone: "UTC-5"  # Optional: Localize to specific regions
        purpose: "Patch deployment"
        notification:
          email: true
          slack: true
          webhook: "https://alerts.example.com"
  degradation:
    thresholds:
      - metric: "request_latency_99th_percentile"
        value: "1000ms"
        action: "disable feature X"
      - metric: "error_rate"
        value: "5%"
        action: "route to fallback service"
  recovery:
    rto: "15 minutes"  # Max time to restore service after failure
    rpo: "5 minutes"   # Max acceptable data loss
  compliance:
    slas: ["GDPR", "SOC2"]
    notes: "Must meet 99.9% uptime for critical transactions."
```

### **2. Endpoint-Specific Guidelines**
Extend the schema for individual endpoints (e.g., REST APIs):

```yaml
endpoints:
  - path: "/v1/auth/login"
    availability:
      slo: 99.9%  # Overrides service-level SLO if specified
      max_retries: 3
      retry_backoff:
        base: 100ms
        max: 5s
      fallback:
        enabled: true
        target: "/v1/auth/fallback"
      error_codes:
        - "429"  # Rate limiting
          action: "throttle client"
```

### **3. Retention Policy**
```yaml
retention:
  metrics: "30 days"
  logs:
    - "error_logs": "90 days"
    - "audit_logs": "180 days"
  failed_requests: "7 days"
```

---

## **Implementation Examples**

### **1. Configuring Availability in a Configuration File**
Save the `availability` schema as `availability.yaml` for a microservice:

```yaml
# availability.yaml
availability:
  name: "Order Service"
  slo:
    target: 99.9%
    measurement_window: "24 hours"
  maintenance:
    windows:
      - start: "2024-01-01T03:00:00Z"
        end:   "2024-01-01T05:00:00Z"
        timezone: "America/New_York"
        purpose: "Database schema migration"
  degradation:
    thresholds:
      - metric: "cpu_usage"
        value: "90%"
        action: "pause non-critical jobs"
```

### **2. Programmatic Enforcement (Python Example)**
Use the schema in code to enforce availability rules:

```python
from pydantic import BaseModel
from datetime import datetime, timezone

class MaintenanceWindow(BaseModel):
    start: datetime
    end: datetime
    timezone: str
    purpose: str

class AvailabilityGuidelines(BaseModel):
    name: str
    slo: dict
    maintenance: dict[str, list[MaintenanceWindow]]

# Example usage:
guides = AvailabilityGuidelines(
    name="Payment Service",
    slo={"target": "99.99%"},
    maintenance={
        "windows": [
            MaintenanceWindow(
                start=datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, 4, 0, 0, tzinfo=timezone.utc),
                timezone="UTC-8",
                purpose="Security patch"
            )
        ]
    }
)

# Validate if current time is in a maintenance window
def is_maintenance(window: MaintenanceWindow) -> bool:
    now = datetime.now(timezone.utc)
    return window.start <= now <= window.end

if is_maintenance(guides.maintenance["windows"][0]):
    print("Service is undergoing maintenance.")
```

### **3. API Response for Availability Status**
Return a standardized availability status endpoint (e.g., `/health/availability`):

```json
{
  "service": "User Service",
  "status": "degraded",
  "slo": {
    "target": 99.95,
    "current": 99.9,
    "window_end": "2024-01-01T06:00:00Z"
  },
  "degradation": {
    "active": true,
    "reason": "High CPU load",
    "affected_endpoints": ["/v1/users/profile"]
  },
  "maintenance_windows": [
    {
      "start": "2024-01-01T02:00:00Z",
      "end": "2024-01-01T04:00:00Z"
    }
  ]
}
```

---

## **Query Examples**

### **1. Check Current Service Status**
```bash
curl -X GET "http://api.example.com/v1/health/availability"
```
**Response:**
```json
{
  "status": "operational",
  "slo": {
    "current": 99.98,
    "target": 99.95
  }
}
```

### **2. List Upcoming Maintenance Windows**
```bash
curl -X GET "http://api.example.com/v1/availability/maintenance?after=2024-01-01"
```
**Response:**
```json
[
  {
    "start": "2024-01-01T02:00:00Z",
    "end": "2024-01-01T04:00:00Z",
    "purpose": "Patch deployment"
  }
]
```

### **3. Query Degradation Thresholds**
```bash
curl -X GET "http://api.example.com/v1/availability/degradation"
```
**Response:**
```json
{
  "thresholds": [
    {
      "metric": "error_rate",
      "value": 0.05,
      "action": "route_to_fallback"
    }
  ]
}
```

---

## **Tools and Libraries**
| **Tool**               | **Purpose**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Prometheus**          | Monitor metrics and enforce degradation thresholds.                         |
| **Grafana**             | Visualize availability trends and SLO compliance.                            |
| **PagerDuty/OpsGenie**  | Alert on SLO breaches or maintenance windows.                               |
| **Terraform**           | Enforce availability rules in infrastructure-as-code (e.g., auto-scaling).  |
| **OpenTelemetry**       | Collect telemetry for availability reporting.                                |

---

## **Best Practices**
1. **Align with Business Goals**: Tailor SLOs to critical vs. non-critical services.
2. **Document Maintenance**: Notify users via multiple channels (email, API calls).
3. **Automate Recovery**: Use CI/CD pipelines to auto-rollback failed deployments.
4. **Monitor SLOs Proactively**: Set up dashboards for real-time compliance tracking.
5. **Test Degradation Paths**: Validate fallback mechanisms during load tests.

---

## **Related Patterns**
1. **[Circuit Breaker Pattern]**
   - Use circuit breakers to stop cascading failures during degradation.
2. **[Bulkhead Pattern]**
   - Isolate components to prevent one failure from affecting the entire service.
3. **[Rate Limiting Pattern]**
   - Control request volume to prevent overload during partial outages.
4. **[Retry Pattern]**
   - Define retry policies for transient failures (align with `max_retries` in endpoints).
5. **[Chaos Engineering]**
   - Experimentally test availability guidelines by injecting failures.
6. **[Configurable Failover]**
   - Dynamically route traffic to healthy instances during outages.
7. **[Feature Flags]**
   - Toggle non-critical features during degradation (complements `degradation.thresholds`).

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **SLO not met**                    | Investigate root cause (e.g., dependency failure) and adjust thresholds.    |
| **Maintenance notification missed** | Verify email/SMS delivery and test webhook integrations.                     |
| **Degradation rules not triggered** | Validate metrics collection (e.g., Prometheus scrape intervals).             |
| **API responses inconsistent**      | Ensure endpoint-specific availability rules are applied uniformly.           |

---
**See Also:**
- [Service Level Indicator (SLI) Pattern](link)
- [Blended Rate Pattern](link) for composite SLO calculations.