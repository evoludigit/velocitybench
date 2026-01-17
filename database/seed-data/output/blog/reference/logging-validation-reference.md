# **[Pattern] Logging Validation – Reference Guide**

---

## **Overview**
**Logging Validation** ensures logs are structurally consistent, accurate, and actionable by validating their content before processing or analysis. This pattern enforces compliance, enhances debugging, and reduces false positives in log-based monitoring, security, and troubleshooting workflows.

Key benefits include:
- **Data integrity** (preventing malformed logs from reaching downstream systems).
- **Consistent formatting** (simplifying parsing and querying).
- **Early error detection** (identifying log corruption or misconfiguration).
- **Compliance adherence** (meeting SLAs, audit logs, or regulatory requirements).

Validation rules are typically defined as **schemas** (e.g., JSON Schema, YAML, or custom regex) and applied at log ingestion, transformation, or storage stages.

---

## **Implementation Details**

### **1. Core Validation Types**
| **Type**               | **Description**                                                                 | **Example Use Cases**                          |
|------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Schema Validation**  | Enforces log structure via JSON/YAML/Protobuf schemas.                        | API gateway logs, application metrics.        |
| **Syntax Validation**  | Checks log format against regex or pattern constraints.                        | Syslog/RFC-standard logs.                     |
| **Semantic Validation**| Validates meaning (e.g., timestamps, status codes, or field value ranges).      | HTTP status codes (200-599), log levels.      |
| **Content Validation** | Ensures required fields exist and are non-null.                                | Database query logs (missing SQL queries).    |

### **2. Validation Phases**
Validation can occur at multiple stages in the log pipeline:

| **Phase**               | **When Applied**                          | **Tools/Techniques**                          |
|-------------------------|-------------------------------------------|-----------------------------------------------|
| **Ingestion**           | During log collection (e.g., agents, proxies). | Fluentd, Logstash filters, AWS Kinesis rules. |
| **Processing**          | During log parsing or enrichment.         | ELK pipeline scripts, Splunk TA (Transforms). |
| **Storage**             | Before writing to databases (e.g., ELK, BigQuery). | Custom validation scripts, database triggers. |

### **3. Key Concepts**
- **Schema-Based Validation**:
  - Define log structure as a schema (e.g., `{ "timestamp": "YYYY-MM-DD", "level": ["INFO", "ERROR", "WARN"] }`).
  - Tools: JSON Schema, Protocols Buffers, YAML.
- **Dynamic Validation**:
  - Adjust rules based on log type (e.g., stricter validation for security logs).
  - Example: Validate `authentication_error` fields only for auth logs.
- **Graceful Handling**:
  - Log validation errors separately (e.g., to a `validation_errors` bucket).
  - Example:
    ```json
    {
      "message": "Invalid log: missing 'user_id' field",
      "original_log": "{\"level\": \"ERROR\", \"message\": \"Failed login\"}",
      "timestamp": "2023-10-01T12:00:00Z"
    }
    ```

---

## **Schema Reference**

Below are common schema templates for popular log formats. Customize fields as needed.

### **1. JSON Log Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ServiceApplicationLog",
  "description": "Schema for application service logs.",
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 formatted timestamp."
    },
    "level": {
      "type": "string",
      "enum": ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"],
      "description": "Log severity level."
    },
    "message": {
      "type": "string",
      "description": "Human-readable log message."
    },
    "source": {
      "type": "string",
      "description": "Component generating the log (e.g., 'api', 'db')."
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true,
      "description": "Key-value pairs of additional context."
    }
  },
  "required": ["timestamp", "level", "message"],
  "additionalProperties": false
}
```

### **2. Syslog Schema**
```yaml
# YAML Schema for Syslog (RFC 5424)
spec:
  type: object
  properties:
    PRI: { type: integer, description: "Priority (e.g., 4*8 + 3 for 'ERR')." }
    VERSION: { type: integer, enum: [1], description: "Syslog version." }
    HOSTNAME: { type: string, description: "Log source hostname." }
    APPNAME: { type: string, description: "Application name." }
    PROCID: { type: string, description: "Process ID." }
    MSGID: { type: string, description: "Message ID." }
    STRUCTURED_DATA: {
      type: array,
      items: { type: string, pattern: "^<[0-9]+>\"[^\"]+\"" }
    }
    TIMESTAMP: { type: string, pattern: "^[0-9]{8}T[0-9]{6}Z$" }
    HOSTNAME: { type: string }
    PROGRAM: { type: string }
    MESSAGE: { type: string }
  required: ["TIMESTAMP", "HOSTNAME", "PROGRAM", "MESSAGE"]
```

### **3. Semantic Validation Rules**
| **Rule**                          | **Validation Logic**                                                                 | **Example**                                  |
|-----------------------------------|------------------------------------------------------------------------------------|----------------------------------------------|
| Timestamp Format                  | Ensure `YYYY-MM-DDTHH:mm:ssZ` format.                                               | `2023-10-01T12:00:00Z` ✅ / `12:00` ❌       |
| HTTP Status Codes                 | Validate status codes are within 100–599.                                          | `404` ✅ / `600` ❌                           |
| Log Level Enum                    | Restrict `level` to predefined values.                                            | `"ERROR"` ✅ / `"ALERT"` ❌                  |
| Required Fields                   | Check presence of critical fields (e.g., `user_id` in auth logs).                  | `{"user_id": "u123"}` ✅ / `{}` ❌             |
| Custom Regex                      | Enforce field patterns (e.g., email format).                                      | `user@example.com` ✅ / `invalid` ❌           |

---

## **Query Examples**

### **1. Validate Logs in ELK (Kibana)**
Use **Ingest Pipelines** to validate logs before indexing:
```json
PUT _ingest/pipeline/log-validator
{
  "description": "Validate JSON logs against schema.",
  "processors": [
    {
      "script": {
        "source": """
          ctx.valid = ctx._source instanceof Object &&
                     'timestamp' in ctx._source &&
                     ctx._source.level in ['INFO', 'ERROR', 'WARN'];
        """
      }
    },
    {
      "set": {
        "field": "validation_status",
        "value": "{{ctx.valid ? 'valid' : 'invalid'}}"
      }
    }
  ]
}
```
**Apply the pipeline when indexing:**
```json
POST _doc/log-12345?pipeline=log-validator
{
  "timestamp": "2023-10-01T12:00:00Z",
  "level": "ERROR",
  "message": "DB connection failed"
}
```

### **2. Validate Logs in Kubernetes**
Use **Logonet** or **Fluent Bit** to filter invalid logs:
```conf
[FILTER]
    Name                grep
    Match               kubernetes.*
    Regex               ^.*?(?:"level":"(INFO|WARN|ERROR)".*)$
    Keep_Long_Tags      No
```
**Query invalid logs in Prometheus/Grafana:**
```promql
sum by (level) (
  count_over_time(
    {job="kubernetes-pods", level!~"INFO|WARN|ERROR"}
    [5m]
  )
) > 0
```

### **3. Validate Logs in AWS CloudWatch**
Use **Lambda** to validate logs before storing:
```python
import json
import jsonschema

schema = {
  "type": "object",
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "level": {"enum": ["INFO", "ERROR"]}
  },
  "required": ["timestamp", "level"]
}

def lambda_handler(event, context):
    for record in event["records"]:
        log_data = json.loads(record["data"])
        try:
            jsonschema.validate(instance=log_data, schema=schema)
            record["result"] = "Ok"
        except jsonschema.ValidationError:
            record["result"] = "Dropped"
    return {"records": event["records"]}
```

---

## **Related Patterns**

| **Pattern**                  | **Description**                                                                                     | **When to Use**                                  |
|------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Structured Logging](#)** | Emits logs in machine-readable formats (JSON, Protobuf).                                            | When parsing/log analysis is critical.           |
| **[Log Sampling](#)**       | Randomly samples logs to reduce volume while preserving trends.                                      | High-volume systems (e.g., microservices).       |
| **[Centralized Logging](#)** | Aggregates logs from multiple sources to a single system (e.g., ELK, Datadog).                     | Distributed applications.                        |
| **[Log Retention Policies](#)** | Defines rules for log storage duration and cleanup.                                                 | Compliance/regulatory requirements.              |
| **[Anomaly Detection](#)**  | Uses ML to flag unusual log patterns (e.g., spikes in errors).                                      | Proactive monitoring.                            |

---

## **Best Practices**
1. **Start Simple**:
   - Begin with basic schema validation (e.g., required fields) before adding complex rules.
2. **Define Failure Modes**:
   - Decide whether invalid logs are dropped, flagged, or routed to a separate bucket.
3. **Monitor Validation Failures**:
   - Track metrics for validation errors (e.g., "Logs dropped due to missing `timestamp`").
4. **Document Schemas**:
   - Publish schemas (e.g., in a Git repo) to ensure consistency across teams.
5. **Test Edge Cases**:
   - Validate malformed logs, missing fields, and unexpected formats in staging.

---
**References**:
- [JSON Schema Specification](https://json-schema.org/)
- [Syslog RFC 5424](https://tools.ietf.org/html/rfc5424)
- [ELK Ingest Pipelines](https://www.elastic.co/guide/en/elasticsearch/reference/current/ingest.html)