# **[Pattern] Data Format Evolution Reference Guide**

---

## **Overview**
The **Data Format Evolution** pattern addresses the common challenge of managing schema changes in modern data systems over time. Whether working with databases, APIs, event streams, or file-based data, schemas inevitably evolve due to business needs, bug fixes, or technological improvements. This pattern provides a systematic approach to handling backward compatibility, versioning, and migration paths while minimizing disruption to existing consumers.

Key principles include:
- **Backward Compatibility**: Ensuring existing systems can still process older data formats.
- **Forward Compatibility**: Allowing new consumers to ignore unknown fields or use defaults.
- **Versioning**: Explicitly tracking schema changes to enable controlled migrations.
- **Data Transformation**: Providing mechanisms to convert between versions during ingestion or query time.

This guide outlines implementation best practices, schema reference standards, query examples, and related patterns to help architects and engineers design resilient data systems.

---

## **Key Concepts**

### **1. Schema Evolution Strategies**
| Strategy               | Description                                                                                                                                                                                                 | Use Case                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Backward-Compatible** | New schemas maintain support for old fields or add optional defaults.                                                                                                                                      | API responses, event schemas where clients may not update immediately.                     |
| **Backward-Incompatible** | Breaking changes (e.g., removing fields) require explicit migration.                                                                                                                                    | Legacy system replacements, critical refactoring.                                            |
| **Hybrid Approach**    | Combine backward compatibility with versioned migration paths (e.g., add fields first, then deprecate old ones).                                                                                  | Long-term data lakes or shared schemas among teams.                                          |
| **Schema Registry**    | Centralized repository for schema definitions (e.g., Confluent Schema Registry, Apache Avro/Protobuf).                                                                                              | Real-time systems (Kafka, Pub/Sub) with multiple consumers.                                 |
| **Polyglot Persistence** | Use different schema formats (JSON, Avro, Protobuf) for different teams/data domains.                                                                                                                | Microservices architectures with heterogeneous needs.                                       |

---

### **2. Versioning Schemas**
#### **Versioning Models**
| Model               | Implementation                                                                                                                                                     | Pros                                                                                     | Cons                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Semantic Versioning (SemVer)** | `major.minor.patch` (e.g., `1.2.3`). Major breaks compatibility; minor/patch add/remove optional fields.                                                        | Standardized, easy to communicate changes.                                                | Overkill for simple schema changes; may require manual migration paths.                  |
| **Timestamp-Based** | Version tied to a Unix timestamp (e.g., `20240101`).                                                                                                               | Simple to generate, reflects chronological order.                                          | No semantic meaning; harder to rollback.                                                 |
| **UUID/GUID**       | Randomly generated IDs for each schema.                                                                                                                          | No conflicts with numeric versions.                                                         | Unintuitive for humans; no inherent order.                                               |
| **Implicit Versioning** | Version inferred from field presence/absence (e.g., `is_premium_customer` field indicates v2).                                                                   | No explicit version field; compact schemas.                                                | Risk of ambiguity; harder to debug.                                                      |
| **Explicit Version Field** | Schema includes a `schema_version` field (e.g., `{"schema_version": 2, ...}`).                                                                           | Explicit control; easy to filter/query.                                                   | Adds overhead; may break existing parsers if not optional.                                |

**Recommendation**: Use **SemVer** for public APIs or shared schemas. For internal systems, **explicit version fields** (with optional defaults) simplify migration.

---

### **2. Data Transformation Techniques**
| Technique               | Description                                                                                                                                                     | Tools/Libraries                                                                          | Use Case                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Schema Registry**     | Centralized registry for schemas (e.g., Avro, Protobuf) with automatic backward/forward conversion.                                                             | Confluent Schema Registry, Apache Avro, Protobuf.                                        | Event-driven systems (Kafka, Pulsar).                                                     |
| **JSON Schema Validation** | Use `draft-07` or later for dynamic typing and optional fields.                                                                                               | `jsonschema`, `ajv`, OpenAPI.                                                               | REST APIs, document databases (MongoDB).                                                   |
| **Custom Transformers** | Write logic to convert between versions (e.g., map old `user.id` to new `user.user_id`).                                                                   | Python (`pandas`, `great-expectations`), JavaScript (`Lodash`), Spark.                    | Batch pipelines, ETL jobs.                                                                |
| **Query-Time Filtering** | Use SQL or NoSQL queries to ignore/rewrite fields during reads.                                                                                               | PostgreSQL (`COALESCE`), MongoDB (`$ifNull`), Athena (`ISNULL`).                           | Analytics queries where full migration isn’t feasible.                                     |
| **Shadow Fields**       | Duplicate fields with version-specific prefixes (e.g., `email_v1`, `email_v2`) until migration completes.                                                       | Custom ETL scripts, database triggers.                                                   | Critical fields where downtime isn’t acceptable.                                          |

---

## **3. Schema Reference**
### **Schema Evolution Example (JSON)**
Below is a **step-by-step evolution** of a user profile schema, demonstrating backward/forward compatibility.

#### **Schema v1 (`2023-10-01`)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserProfile/v1",
  "type": "object",
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "email": { "type": "string", "format": "email" },
    "created_at": { "type": "string", "format": "date-time" }
  },
  "required": ["user_id", "name", "email", "created_at"],
  "additionalProperties": false
}
```

#### **Schema v2 (`2024-01-15`)**
- **Adds**: `is_premium` (optional), `last_login` (optional).
- **Backward-compatible**: All v1 fields remain required; new fields default to `null`/`false`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserProfile/v2",
  "type": "object",
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "email": { "type": "string", "format": "email" },
    "created_at": { "type": "string", "format": "date-time" },
    "is_premium": { "type": "boolean", "default": false },
    "last_login": { "type": "string", "format": "date-time" }
  },
  "required": ["user_id", "name", "email", "created_at"],
  "additionalProperties": true
}
```

#### **Schema v3 (`2024-03-10`)**
- **Removes**: `email` (deprecated in favor of `user_id + auth_provider`).
- **Breaking change**: Requires migration script to replace `email` with `auth_provider.email`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UserProfile/v3",
  "type": "object",
  "properties": {
    "user_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "is_premium": { "type": "boolean", "default": false },
    "last_login": { "type": "string", "format": "date-time" },
    "auth_provider": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["email", "social"] },
        "email": { "type": "string", "format": "email" }
      },
      "required": ["type"]
    }
  },
  "required": ["user_id", "name", "created_at", "auth_provider"],
  "additionalProperties": true
}
```

---

## **4. Query Examples**
### **Handling Schema Evolution in SQL**
#### **PostgreSQL: Ignore Unknown Columns**
```sql
-- Query v1 and v2 data together (v3 drops 'email')
SELECT
  user_id,
  name,
  COALESCE(email, auth_provider->>'email') AS email,
  is_premium,
  last_login
FROM user_profiles
-- Use JSON functions for dynamic fields
WHERE jsonb_typeof(raw_data::jsonb) IN ('object', 'null');
```

#### **MongoDB: Schema Agnostic Query**
```javascript
// Query all user profiles, handling missing fields
db.user_profiles.find({
  $or: [
    { "raw_data.email": { $exists: true } },  // v1/v2
    { "raw_data.auth_provider.email": { $exists: true } }  // v3
  ]
});
```

### **Python (Pandas): Dynamic Parsing**
```python
import pandas as pd
from great_expectations import Validator

# Load data with unknown columns
df = pd.read_json("user_profiles.jsonl")

# Validate and transform
validator = Validator(df)
validator.expect_column_values_to_be_of_type("user_id", "str")
validator.expect_column_values_to_match_regex("user_id", r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Handle email migration (v1->v3)
if "email" in df.columns and "auth_provider" not in df.columns:
    df["auth_provider"] = df["email"].apply(lambda x: {"type": "email", "email": x}).astype(str)
    df.drop("email", axis=1, inplace=True)
```

### **Avro/Schema Registry (Kafka)**
```java
// Producer: Emit v2 data with backward compatibility
Schema schema = new Schema.Parser().parse(
    "{ " +
    "  \"type\": \"record\", \"name\": \"UserProfile\", \"fields\": [ " +
    "    {\"name\": \"user_id\", \"type\": \"string\"}, " +
    "    {\"name\": \"name\", \"type\": \"string\"}, " +
    "    {\"name\": \"email\", \"type\": \"string\"}, " +
    "    {\"name\": "is_premium", "type\": {\"type\": \"boolean\", \"default\": false}}, " +
    "    {\"name\": \"last_login\", \"type\": [\"null\", \"string\"]} " +
    "  ]" +
    "}"
);

ProducerRecord<String, GenericRecord> record = new ProducerRecord<>(
    "user_topic",
    schema.name(),
    new GenericData.Record(schema),
    // Set fields...
);
```

---

## **5. Best Practices**
### **Mitigating Risks**
| Risk                        | Mitigation Strategy                                                                                                                                                                                                 |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consumer Breakage**       | Use feature flags for new fields; deprecate old fields gradually.                                                                                                                                               |
| **Data Loss**               | Validate schema evolution scripts in staging; use idempotent transformations.                                                                                                                                     |
| **Performance Overhead**    | Cache schema metadata; use columnar storage (Parquet) for efficient querying.                                                                                                                                  |
| **Version Chaos**           | Enforce schema governance (e.g., review boards for breaking changes).                                                                                                                                          |
| **Tooling Gaps**            | Invest in schema registry (e.g., Confluent, AWS Glue) for automated validation.                                                                                                                                   |

### **Migration Checklist**
1. **Assess Impact**: Identify consumers/producers of each schema.
2. **Test Backward/Forward Compatibility**: Validate with sample data.
3. **Implement Gradual Rollout**:
   - Add new fields first.
   - Deprecate old fields with warnings (e.g., `deprecated_since: "2024-05-01"`).
4. **Monitor**: Track schema usage (e.g., CloudWatch for API calls, Kafka consumer lag).
5. **Document**: Update READMEs with migration paths and deprecated fields.

---

## **6. Related Patterns**
| Pattern                        | Description                                                                                                                                                                                                 | When to Use                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Polyglot Persistence](https://patterns.dev/goto/polyglot)** | Use multiple data formats/storage engines for different teams.                                                                                                                                          | Microservices with heterogeneous needs (e.g., NoSQL for flexibility, SQL for analytics).       |
| **[Event Sourcing](https://patterns.dev/goto/event-sourcing)** | Store state changes as immutable events; leverage schema evolution for event schemas.                                                                                                                    | Audit logs, financial systems, or systems requiring full history.                                |
| **[CQRS](https://patterns.dev/goto/cqrs)**         | Separate read/write models; evolve read models independently.                                                                                                                                             | High-throughput systems where writes are more volatile than reads.                               |
| **[Data Vault](https://patterns.dev/goto/data-vault)** | Centralized data warehouse with hubs/links; schema evolution viaSatellite tables.                                                                                                                       | Enterprise data lakes requiring auditability and backward compatibility.                        |
| **[Schema-as-Code](https://patterns.dev/goto/schema-as-code)** | Treat schemas as source code (e.g., Terraform for databases).                                                                                                                                             | Infrastructure-as-code (IaC) environments with CI/CD pipelines.                                  |
| **[Record Linkage](https://patterns.dev/goto/record-linkage)** | Reconcile data from evolved schemas (e.g., matching `user_id` across versions).                                                                                                                              | Data integration projects with historical data.                                                 |

---

## **7. Tools & Libraries**
| Category               | Tools/Libraries                                                                                                                                                     | Key Features                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Schema Validation**  | [JSON Schema](https://json-schema.org/), [Avro](https://avro.apache.org/), [Protobuf](https://developers.google.com/protocol-buffers)                          | Backward/forward compatibility, compact binary formats.                                         |
| **Schema Registry**    | [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html), [AWS Glue DataBrew](https://aws.amazon.com/glue/databrew/) | Centralized governance, evolution tracking.                                                       |
| **ETL/Transformation** | [Apache Spark](https://spark.apache.org/), [Airflow](https://airflow.apache.org/), [dbt](https://www.getdbt.com/)                                                       | SQL-based transformations, macro support for schema evolution.                                  |
| **Database**           | [PostgreSQL](https://www.postgresql.org/) (JSONB), [MongoDB](https://www.mongodb.com/), [DynamoDB](https://aws.amazon.com/dynamodb/)                                | Native support for nested JSON/semi-structured data.                                             |
| **Monitoring**         | [Great Expectations](https://greatexpectations.io/), [Deequ](https://deequ.readthedocs.io/en/latest/)                                                              | Data quality checks for schema compliance.                                                       |

---
**Note**: For production systems, combine multiple tools (e.g., Schema Registry + dbt + Great Expectations) for end-to-end observability.