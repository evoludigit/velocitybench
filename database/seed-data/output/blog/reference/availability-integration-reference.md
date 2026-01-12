---

# **[Pattern] Availability Integration Reference Guide**

---

## **Overview**
The **Availability Integration** pattern ensures seamless synchronization between your application’s availability status and external systems (e.g., monitoring tools, notification services, SaaS platforms). This pattern standardizes how applications expose availability states (e.g., `UP`, `DEGRADED`, `DOWN`) so third-party systems can respond dynamically—triggering alerts, adjusting scaling policies, or enabling fallback mechanisms.

The pattern is critical for **resilience**, **observability**, and **automated recovery**. It decouples availability logic from business logic while enabling real-time collaboration between systems. Common use cases include:
- **Monitoring systems** (e.g., Prometheus, Datadog) consuming availability updates for alerting.
- **Orchestration platforms** (e.g., Kubernetes, AWS Auto Scaling) adjusting capacity based on health.
- **Customer-facing systems** (e.g., chatbots, APIs) providing accurate uptime/downtime notifications.

---

## **Key Concepts**
### **1. Availability States**
A finite set of discrete states that describe an application’s operational health. Example states:
| State      | Description                                                                 | Recommended Triggers                                                                 |
|------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `UP`       | Fully operational.                                                         | Passing health checks, no active failures.                                         |
| `DEGRADED` | Partially functional (e.g., warnings, throttling, or non-critical failures). | Deprecated features, performance degradations, or recoverable errors.                |
| `DOWN`     | Unavailable (critical failures).                                            | Unrecoverable errors, dependency outages, or manual shutdowns.                     |
| `UNKNOWN`  | State cannot be determined (e.g., timeout during health check).             | Temporary network issues or unreachable endpoints.                                 |
| `MAINTENANCE`| Planned downtime (optional state).                                        | Scheduled deployments or infrastructure updates.                                   |

---
### **2. Integration Modes**
Define how availability data flows between systems:
| Mode          | Description                                                                 | Use Case Example                                                                 |
|---------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Polling**   | External systems query the application’s availability at intervals.          | Monitoring agents checking `/health` endpoints every 30 seconds.                  |
| **Push**      | The application emits availability changes to external systems via events.    | Webhooks to Slack or PagerDuty on state transitions.                             |
| **Hybrid**    | Combines polling (for reliability) and push (for immediacy).               | Polling for production systems + push for critical alerts.                        |

---
### **3. Event Payload Structure**
Standardized JSON payload for push-based integrations:
```json
{
  "service_id": "order-service-v1",
  "timestamp": "2024-07-20T14:30:00Z",
  "state": "DOWN",
  "reason": "Database connection timeout (failed 5/5 retries)",
  "severity": "CRITICAL",
  "details": {
    "error_code": "DB_CONNECTION_ERROR",
    "duration": "PT15M", // ISO 8601 duration
    "affected_resources": ["payment-gateway"]
  },
  "resolved_at": null, // Filled if state transitions back to UP/DEGRADED
  "metadata": {
    "version": "1.0",
    "env": "production"
  }
}
```

---
### **4. Health Check Endpoints**
REST endpoints for polling-based integrations:
| Endpoint          | Method | Description                                                                 | Example Response                                                                 |
|-------------------|--------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `/health`        | `GET`  | Basic availability (UP/DOWN).                                               | `{"status": "UP"}`                                                              |
| `/health/extended`| `GET`  | Detailed state (UP/DEGRADED/DOWN/UNKNOWN) with metadata.                   | `{ "status": "DEGRADED", "warnings": ["Slow response times"] }`                   |
| `/health/events` | `GET`  | Historical availability events (paginated).                                  | `[{ "timestamp": "2024-07-19T10:00:00Z", "state": "DOWN" }]`                     |

---
### **5. Validation Rules**
Ensure data integrity across systems:
- **Idempotency**: Push events must be retried safely (e.g., include `event_id` for deduplication).
- **TTL**: Events expire after **24 hours** (configurable) to prevent stale data.
- **Rate Limiting**: No more than **10 events/second** per service (adjustable).
- **Schema Compliance**: All payloads must validate against the [JSON Schema](#schema-reference).

---

## **Schema Reference**
### **1. Availability State Schema (`availability_state.json`)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "service_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9-]+([a-zA-Z0-9-]+\/)*[a-zA-Z0-9-]+$",
      "description": "Unique identifier for the service (e.g., `order-service-v1`)."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "UTC ISO 8601 timestamp of the event."
    },
    "state": {
      "type": "string",
      "enum": ["UP", "DEGRADED", "DOWN", "UNKNOWN", "MAINTENANCE"],
      "description": "Current availability state."
    },
    "severity": {
      "type": "string",
      "enum": ["NONE", "INFO", "WARNING", "CRITICAL"],
      "description": "Severity level (maps to downstream alerting rules)."
    },
    "reason": {
      "type": "string",
      "description": "Human-readable explanation (truncated to 500 chars)."
    },
    "details": {
      "type": "object",
      "additionalProperties": true,
      "description": "Machine-readable context (e.g., error codes)."
    },
    "resolved_at": {
      "type": "string",
      "format": "date-time",
      "nullable": true,
      "description": "Timestamp when the issue was resolved (if applicable)."
    },
    "metadata": {
      "type": "object",
      "properties": {
        "version": { "type": "string" },
        "env": { "type": "string", "enum": ["development", "staging", "production"] }
      }
    }
  },
  "required": ["service_id", "timestamp", "state", "severity"]
}
```

---
### **2. Health Endpoint Response Schema (`health_response.json`)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["UP", "DEGRADED", "DOWN", "UNKNOWN"]
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of non-critical issues (e.g., ["Slow API response"])."
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    },
    "tracing_id": {
      "type": "string",
      "description": "Correlation ID for debugging."
    }
  },
  "required": ["status"]
}
```

---
### **3. Validation Tool**
Use [jsonschema](https://github.com/Julian/jsonschema) to validate payloads:
```bash
npm install jsonschema
node -e "require('jsonschema').validate(JSON.parse(require('./payload.json')), require('./availability_state.json'))"
```

---

## **Query Examples**
### **1. Polling a Health Endpoint (cURL)**
```bash
# Check basic status
curl -s http://api.example.com/health | jq '.status'

# Check extended health with warnings
curl -s http://api.example.com/health/extended | jq '.warnings'
```

---
### **2. Subscribing to Push Events (Webhook Setup)**
**Example Webhook Payload (Flask/Python):**
```python
from flask import Flask, request, jsonify
import jsonschema

app = Flask(__name__)

SCHEMA = {...}  # Load schema from file

@app.route('/health-events', methods=['POST'])
def handle_event():
    payload = request.json
    try:
        jsonschema.validate(payload, SCHEMA)
        if payload["state"] == "DOWN":
            send_alert(payload["reason"])
        return jsonify({"status": "received"}), 200
    except jsonschema.ValidationError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000)
```

---
### **3. Filtering Historical Events (API Query)**
```bash
# Fetch events for a service in the last 24 hours
curl -s "http://monitoring.example.com/api/events?service_id=order-service-v1&since=2024-07-19T00:00:00Z" | jq '.[] | select(.state == "DOWN")'
```

---
### **4. Automated Scaling (Terraform Example)**
```hcl
resource "aws_autoscaling_policy" "health_based_scaling" {
  name         = "availability-down-scaling"
  policy_type  = "StepScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -2  # Reduce capacity by 2 units
  }

  # Trigger scaling when health state is DOWN
  trigger {
    metric = "AvailabilityState"
    value  = "DOWN"
    dimension {
      name   = "ServiceID"
      value  = "order-service-v1"
    }
  }
}
```

---

## **Implementation Steps**
### **1. Define Availability States**
- Map your application’s errors to states (e.g., `5xx` errors → `DOWN`).
- Document thresholds for `DEGRADED` (e.g., >95% latency).

### **2. Choose Integration Mode**
| Mode      | Implementation Notes                                                                 |
|-----------|---------------------------------------------------------------------------------------|
| **Polling**| Expose `/health` endpoints with caching (e.g., 30s TTL).                              |
| **Push**   | Use a pub/sub system (e.g., Kafka, AWS SNS) to distribute events.                      |
| **Hybrid** | Combine both (e.g., push for alerts, polling for orchestration).                       |

### **3. Implement Health Checks**
- **End-to-End Checks**: Validate dependencies (e.g., database, external APIs).
- **Liveness Probe**: Short-lived check (e.g., `/health/liveness`).
- **Readiness Probe**: Longer check (e.g., `/health/readiness`).

### **4. Validate Payloads**
- Use tools like [JSON Schema](https://json-schema.org/) or [OpenAPI](https://swagger.io/specification/) for validation.
- Log invalid payloads for debugging.

### **5. Integrate with External Systems**
- **Monitoring**: Expose metrics to Prometheus (`availability_state` gauge).
- **Alerting**: Map states to alert rules (e.g., `DOWN` → P1 alert).
- **Orchestration**: Sync with Kubernetes LivenessProbe or AWS Health Checks.

### **6. Testing**
- **Unit Tests**: Mock health endpoints and verify responses.
- **Chaos Testing**: Simulate failures (e.g., kill a pod) and validate state transitions.
- **Load Testing**: Ensure polling endpoints handle concurrent requests.

---
## **Query Examples (Expanded)**
### **6. Monitoring with Prometheus**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'availability'
    metrics_path: '/health/metrics'
    static_configs:
      - targets: ['api.example.com:8080']
```

**Exposed Metrics:**
| Metric               | Type    | Description                                                |
|----------------------|---------|------------------------------------------------------------|
| `availability_state` | Gauge   | Current state (`UP=1`, `DOWN=0`).                          |
| `event_total`        | Counter | Total events emitted (resets on server restart).          |
| `latency_ms`         | Histogram | Response time for health checks.                          |

---
### **7. Alert Rules (Prometheus)**
```yaml
groups:
- name: availability-alerts
  rules:
  - alert: ServiceDown
    expr: availability_state == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.service_id }} is DOWN"
```

---

## **Error Handling**
### **1. Common Issues & Fixes**
| Issue                          | Cause                          | Solution                                                                 |
|--------------------------------|--------------------------------|-------------------------------------------------------------------------|
| **Schema Validation Fails**    | Payload missing required fields. | Use tools like [jsonlint](https://jsonlint.com/) to validate.             |
| **Push Events Dropped**        | Rate limiting exceeded.        | Implement exponential backoff for retries.                               |
| **Stale Data in Polling**      | Caching TTL too long.          | Reduce TTL to 30s for dynamic states.                                    |
| **Race Conditions**            | Concurrent state updates.      | Use transactional writes (e.g., database locks) for critical paths.      |

---
### **2. Logging Best Practices**
- Log **push event IDs** for debugging retries.
- Include **tracing IDs** (e.g., X-Request-ID) in health check responses.
- Use structured logging (e.g., JSON) for filtering:
  ```json
  {
    "timestamp": "2024-07-20T15:00:00Z",
    "level": "ERROR",
    "message": "Health check failed",
    "service_id": "order-service-v1",
    "error": "Database connection refused",
    "trace_id": "abc123"
  }
  ```

---

## **Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Prevent cascading failures by stopping calls to failing services.        | When dependent services are unstable (e.g., third-party APIs).              |
| **[Bulkhead](https://microservices.io/patterns/reliability/bulkhead.html)**               | Isolate failure domains with thread/process pools.                          | To limit the impact of one failing component on others.                     |
| **[Retry with Exponential Backoff](https://martinfowler.com/articles/retry.html)**       | Retry failed operations with increasing delays.                           | For transient errors (e.g., network timeouts).                            |
| **[Resilience Patterns](https://resilience4j.readme.io/docs/overview)**                  | Framework for implementing retry, circuit breaker, etc.                   | When combining multiple resilience strategies.                             |
| **[Feature Flags](https://launchdarkly.com/patterns/feature-flags/)**                     | Gradually roll out changes without downtime.                               | For zero-downtime deployments or A/B testing.                                |
| **[Saga Pattern](https://microservices.io/patterns/data-management/saga.html)**            | Manage distributed transactions across services.                         | For multi-step workflows requiring compensating actions.                    |

---
## **References**
- **Standards**:
  - [RESTful Health Checks RFC](https://tools.ietf.org/html/rfc6578) (for `/health` endpoints).
  - [OpenTelemetry Health Checks](https://opentelemetry.io/docs/specs/otel/protocol/health/).
- **Tools**:
  - [Prometheus Exporter](https://prometheus.io/docs/instrumenting/exporters/) (for metrics).
  - [Kafka Connect](https://kafka.apache.org/documentation/#connect) (for event streaming).
  - [Postman Collection](https://documenter.getpostman.com/view/12345/abcde) (for API testing).

---
## **Example Implementations**
### **1. Node.js (Express)**
```javascript
const express = require('express');
const jsonschema = require('jsonschema');
const schema = require('./availability_state.json');

const app = express();
app.use(express.json());

// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'UP' });
});

// Webhook receiver
app.post('/health-events', (req, res) => {
  const result = jsonschema.validate(req.body, schema);
  if (!result.valid) {
    return res.status(400).json({ error: result.errors });
  }
  console.log(`Event received: ${req.body.state}`);
  res.status(200).json({ status: 'received' });
});

app.listen(3000, () => console.log('Server running'));
```

---
### **2. Kubernetes Liveness Probe**
```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

---
### **3. AWS Health Checks**
```yaml
# CloudFormation Template
Resources:
  HealthCheck:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      HealthCheck:
        Path: /health
        HealthyThresholdCount: 2
        UnhealthyThresholdCount: 3
        IntervalSeconds: 30
        TimeoutSeconds: 5
```

---
## **Troubleshooting**
### **1. Debugging Push Events**
- **Check Webhook Logs**: Look for `5xx` responses in your receiver’s logs.
- **Verify Retries**: Ensure your client implements exponential backoff.
- **Monitor Latency**: High latency in push events may indicate network issues.

### **2. Polling Performance**
- **Increase TTL**: If endpoints are slow, extend the caching TTL (e.g., to 60s).
- **Compress Responses**: Use gzip for large payload