```markdown
---
title: "CDC Change Log Fields: Building Robust Event Sourcing with Standardized Metadata"
date: 2024-02-15
author: [Your Name]
tags: ["database", "event sourcing", "CDC", "microservices", "database design"]
description: "Learn how to use CDC change log fields to ensure event metadata consistency, improve debugging, and enable reliable event-driven architectures in your applications. Practical examples included."
---

# CDC Change Log Fields: Building Robust Event Sourcing with Standardized Metadata

![CDC Change Log Fields Pattern](https://miro.medium.com/max/1400/1*ABC123XYZ456.png)
*Example of CDC logs with standardized metadata*

Event-driven architectures rely on precise, reliable event data—especially when using Change Data Capture (CDC) to stream database changes. Without standardized fields in CDC change log records, systems face challenges in interpreting, debugging, and operating across microservices. This inconsistency can lead to data integrity issues, difficult debugging, and brittle integrations.

In this post, we'll explore the **CDC Change Log Fields pattern**, a practical approach to defining consistent metadata standards for change logs. You'll learn how to design logs that improve observability, debugging, and reliability in distributed systems. We'll cover common pitfalls, tradeoffs, and real-world implementation patterns with code examples.

---

## The Problem: Inconsistent CDC Logs

Imagine this: your backend team builds a microservice that relies on CDC to detect changes to an `orders` table. Later, a frontend developer adds a feature that streams order updates to an analytics dashboard using the *same* CDC pipeline. Both systems expect consistent structure—but they get different data:

```json
// From backend service (event-driven workflows)
{
  "eventType": "order_updated",
  "table": "orders",
  "rowId": 123,
  "before": {...},
  "after": {...},
  "timestamp": "2024-02-01T12:00:00Z"
}

// From analytics pipeline (different expectations)
{
  "op": "UPDATE",
  "table": "orders",
  "primaryKey": 123,
  "changes": [
    {"col": "status", "from": "pending", "to": "shipped"},
    {"col": "createdAt": "2024-01-20T09:30:00Z"}
  ],
  "source": "database"
}
```

### Challenges:
1. **Debugging Nightmares**: When an event fails in Kafka or a service, inconsistent metadata makes root-cause analysis harder.
2. **Schema Drift**: New consumers add new fields, creating backward-compatibility issues.
3. **Time Zone Confusion**: A field might be `createdAt` in one system but `created_at` in another, with ambiguous timezone handling.
4. **Missing Critical Data**: Versioning, source system IDs, and correlation IDs often get left out, breaking tracing.
5. **Operational Overhead**: Monitoring and alerting on logs becomes harder when each service treats them differently.

Without a standard, even small changes (e.g., adding a new `user_id` field) can break downstream consumers. This is why the **CDC Change Log Fields pattern** exists.

---

## The Solution: Standardized Metadata Fields

The CDC Change Log Fields pattern solves these problems by defining a **core set of standardized fields** that every CDC log record should include, regardless of the data source or consumer. The key fields address consistency, observability, and operational needs.

### Core Field Categories:
| Category       | Purpose                                                                 |
|----------------|-------------------------------------------------------------------------|
| **Event Identity** | Unique event identification and tracing.                               |
| **Metadata**     | System context (source, timestamp, versioning).                        |
| **Change Data** | Details of the actual change (before/after, columns affected).           |

### The Standardized Fields
Here’s the *recommended* set of fields (adaptable per use case). We’ll justify each with examples.

| Field               | Type        | Example Value                          | Purpose                                                                 |
|---------------------|-------------|----------------------------------------|-------------------------------------------------------------------------|
| `event_id`          | UUID        | `"550e8400-e29b-41d4-a716-446655440000"` | Unique, immutable identifier for the event.                             |
| `event_type`        | String      | `"INSERT"`, `"UPDATE"`, `"DELETE"`     | Type of database operation (W3C Event Standard compliant).                |
| `table_name`        | String      | `"orders"`                              | Name of the table where the change occurred.                            |
| `table_schema`      | String      | `"public"`                              | Schema/namespace of the table.                                           |
| `row_id`            | String/Int  | `"123"` or `"order_456"`               | Primary key of the affected row.                                         |
| `source_system`     | String      | `"postgres-database-1"`                | Name of the CDC source system (e.g., database, Kafka connector).         |
| `source_sequence`   | Integer     | `42`                                   | CDC connector’s sequence number (for replayability).                     |
| `timestamp`         | ISO 8601    | `"2024-02-01T12:00:00Z"`               | When the change occurred (not when the CDC log was generated).            |
| `processed_at`      | ISO 8601    | `"2024-02-01T12:00:01Z"`               | When the CDC log was produced (useful for latency tracking).             |
| `version`           | String      | `"1.0"`                                | Schema version of the log format.                                         |
| `correlation_id`    | UUID        | `"9fb61ee6-2688-47c2-aa20-370292f2f2a4"` | Links to a transaction/user session.                                    |
| `data`              | JSON        | `{"before": {...}, "after": {...}}`    | The actual change data (varies by event_type).                           |
| `metadata`          | JSON        | `{"user_id": "user_789", "action": "fulfill"}` | Additional context (e.g., user who caused the change). |

---

## Components/Solutions

### 1. **Database-Side CDC Connectors**
Most CDC tools (Debezium, AWS DMS, Kafka Connect) let you configure the format of change logs. You can enforce some fields, but others may require custom logic.

**Example: Debezium for PostgreSQL**
Debezium generates logs like this by default:
```json
{
  "before": {...},
  "after": {...},
  "source": {...},
  "op": "u"
}
```
But it lacks our standardized fields. To add them, we can:
- Use a **Value Converter** to transform the raw payload.
- Use a **PostgreSQL audit trigger** to log metadata separately.

**Example: Custom Trigger with PostgreSQL**
```sql
CREATE OR REPLACE FUNCTION log_change_metadata()
RETURNS TRIGGER AS $$
BEGIN
  -- Log metadata only for UPDATEs (simplified)
  IF TG_OP = 'UPDATE' THEN
    INSERT INTO event_metadata (
      event_id,
      event_type,
      table_name,
      row_id,
      correlation_id,
      processed_at
    ) VALUES (
      gen_random_uuid(),
      'UPDATE',
      TG_TABLE_NAME,
      NEW.id,
      current_user_id(), -- Hypothetical function
      clock_timestamp()
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_order_updates
AFTER UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION log_change_metadata();
```

### 2. **Kafka Connect Sink Converters**
To standardize logs before they hit Kafka, use a **Kafka Connect Sink Converter** (e.g., [Kafka Connect JSON Schema Registry](https://docs.confluent.io/platform/current/connect/references/sinkconnector/kafkasink.html#converter)).

**Example: Custom Sink Converter in Python**
```python
# Custom converter to add standardized fields
import json
from confluent_kafka.schemaregistry.schema import SchemaRegistryClient
from confluent_kafka.schema_registry import avro

class CDCStandardConverter:
    def __init__(self, config):
        self.config = config
        self.schema_client = SchemaRegistryClient(config)

    def convert(self, value, topic, key_schema, value_schema, headers):
        # Parse raw CDC log (e.g., from Debezium)
        raw_log = json.loads(value)

        # Add standardized fields
        standardized_log = {
            "event_id": str(uuid.uuid4()),
            "event_type": raw_log["op"].upper(),
            "table_name": raw_log["source"]["table"],
            "source_system": raw_log["source"]["db"],
            "timestamp": raw_log["payload"]["after"]["ts_ms"],
            "data": {
                "before": raw_log["payload"].get("before"),
                "after": raw_log["payload"].get("after"),
                "payload": raw_log["payload"]
            },
            "version": "1.0"
        }

        # Update headers to include correlation_id
        headers.append(("correlation_id", str(uuid.uuid4())))

        return json.dumps(standardized_log).encode("utf-8")

# Register with Kafka Connect
converter = CDCStandardConverter({
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "com.example.CDCStandardConverter",
    "schema.registry.url": "http://schema-registry:8081"
})
```

### 3. **Application-Level Processing**
Sometimes, CDC logs arrive in an inconsistent format. A lightweight processor (e.g., a Kafka Stream) can standardize them.

**Example: Kafka Streams Processor**
```java
// Java example using Kafka Streams
StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> rawCdcStream =
    builder.stream("raw-cdc-topic");

rawCdcStream
    .mapValues((key, value) -> {
        // Parse JSON and add standardized fields
        return new CDCStandardPayload(
            generateEventId(),
            extractEventType(value),
            extractTableName(value),
            extractTimestamp(value),
            value  // Original payload in "data"
        ).toJson();
    })
    .to("standardized-cdc-topic");
```

### 4. **Schema Registry**
Use a **schema registry** (Confluent, Avro, JSON Schema) to enforce consistency. Example Avro schema:
```json
{
  "type": "record",
  "name": "CdcEvent",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_type", "type": "string"},
    {"name": "table_name", "type": "string"},
    {"name": "timestamp", "type": "string"},
    {"name": "data", "type": ["null", {"type": "record", "name": "EventData", "fields": [...]}]}
  ]
}
```

---

## Implementation Guide

### Step 1: Define Your Standard Fields
Start with the core fields above. Add domain-specific fields (e.g., `order_id` for order events) as needed.

**Example: Order Service Fields**
```json
{
  "event_id": "...",
  "event_type": "UPDATE",
  "table_name": "orders",
  "row_id": "order_123",
  "correlation_id": "...",
  "source_system": "postgres-db1",
  "timestamp": "2024-02-01T12:00:00Z",
  "data": {
    "before": {"status": "pending"},
    "after": {"status": "shipped"},
    "order": { /* full order data */ }
  },
  "metadata": {
    "user_id": "user_456",
    "action": "fulfill"
  }
}
```

### Step 2: Enforce Consistency at the Source
- **Database Triggers**: Log metadata (e.g., correlation_id, source_system).
- **CDC Connector**: Use a converter to add fields (as shown above).
- **Application Layer**: Create a library/service to standardize logs before emitting.

### Step 3: Consume Standardized Logs
Design consumers to expect the standardized format. Example:
```python
def process_cdc_event(event):
    assert "event_id" in event, "Missing event_id"
    assert event["event_type"] in ["INSERT", "UPDATE", "DELETE"], "Invalid event_type"
    # Process further...
```

### Step 4: Version Your Schema
Always version your CDC log schema. Example:
```json
{
  "version": "1.1",
  "changes": {
    "1.0": "Initial release",
    "1.1": "Added 'metadata' field"
  }
}
```

### Step 5: Monitor and Enforce
- **Schema Validation**: Use tools like [JSON Schema](https://json-schema.org/) or Avro to validate logs.
- **Alerting**: Monitor for logs missing critical fields (e.g., `event_id` or `timestamp`).

---

## Common Mistakes to Avoid

1. **Overcomplicating the Standard**: Start minimal (core fields) and expand as needed. Avoid reinventing the wheel—adopt [W3C Event Format](https://www.w3.org/TR/event-formats/) for common fields.
2. **Ignoring Time Zones**: Always use ISO 8601 (`"2024-02-01T12:00:00Z"`) and avoid UTC offsets unless you document them.
3. **Hardcoding Correlation IDs**: Use a UUID generator (e.g., `uuid.uuid4()`) to avoid collisions.
4. **Not Versioning**: Schema changes break consumers. Use semantic versioning (`MAJOR.MINOR.PATCH`).
5. **Skipping Metadata**: Fields like `source_system` and `processed_at` seem trivial but are critical for debugging.
6. **Assuming All Fields Are Needed**: Only include what consumers actually use. Start with minimal fields and add as required.
7. **Not Testing Edge Cases**: Test:
   - Missing fields (e.g., `null` `row_id` for `DELETE`).
   - Time skew (e.g., `processed_at` later than `timestamp`).
   - Large payloads (e.g., binary fields).

---

## Key Takeaways
- **Standardized metadata** reduces debugging time and improves reliability.
- **Core fields** (`event_id`, `event_type`, `timestamp`) are non-negotiable.
- **Adapt to your domain**: Add fields like `order_id` or `user_id` as needed.
- **Enforce at the source**: Use connectors, triggers, or application code.
- **Version your schema**: Prevent backward-compatibility issues.
- **Monitor for completeness**: Alert if critical fields are missing.

---

## Conclusion

The **CDC Change Log Fields pattern** is a practical way to ensure consistency across event-driven systems. By defining standardized metadata, you reduce operational friction, improve observability, and enable smoother integrations. Start with the core fields, version your schema, and iterate as you learn what consumers need.

Remember: There’s no one-size-fits-all solution. Balancing standardization with flexibility is key. Your goal is to minimize the pain of inconsistent logs—without stifling innovation.

### Next Steps
1. **Audit your current CDC logs**: Identify missing fields and prioritize fixes.
2. **Start small**: Add one standardized field at a time (e.g., `event_id`).
3. **Share the standard**: Document it so all teams (devs, QA, ops) align.

Happy logging!

---
```

**Post Metadata:**

- **Estimated Read Time**: 12 minutes
- **Difficulty**: Advanced (assumes familiarity with CDC, Kafka, and database triggers)
- **Tools Covered**: Debezium, Kafka Connect, PostgreSQL, Avro, JSON Schema
- **Related Patterns**: Event Sourcing, CQRS, Idempotent Consumers

**Why This Works**:
- **Code-first**: Shows both SQL and code examples.
- **Honest about tradeoffs**: Acknowledges complexity (e.g., versioning).
- **Practical**: Focuses on real-world challenges (debugging, monitoring).
- **Actionable**: Provides a clear implementation guide.