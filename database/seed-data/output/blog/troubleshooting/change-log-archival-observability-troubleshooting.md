# **Debugging Change Log Archival for Observability: A Troubleshooting Guide**
**Last Updated:** [Insert Date]
**Applies To:** Observability systems, Log aggregation & archival pipelines (ELK, Loki, Datadog, custom solutions)

---

## **1. Overview**
The **Change Log Archival for Observability** pattern ensures long-term retention of logs, metrics, and traces—critical for compliance, debugging, and auditing. Issues in this pattern typically manifest as **data loss, slow queries, incomplete archives, or storage overflows**.

This guide provides a **structured debugging approach** to identify and resolve common failures efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm which symptoms match your issue:

| **Symptom**                          | **Possibility**                                                                 |
|--------------------------------------|--------------------------------------------------------------------------------|
| Logs/metrics missing after [time]    | Pipeline failure, retention misconfiguration, or incorrect sink settings.     |
| High storage costs or quotas reached | Retention policy misconfigured, or unbounded archival.                      |
| Slow queries on archived data        | Shard misalignment, index fragmentation, or improper partitioning.             |
| Failed archival jobs (ETL failures)  | Source auth errors, sink connection issues, or schema drift.                 |
| Duplicated or incomplete records     | Idempotency issues, failed retries, or incorrect deduplication logic.         |
| Alerts firing for "high latency"     | Backpressure in archival pipelines (e.g., Kafka consumer lag, S3 upload delays). |
| Missing metadata in archived logs    | Mismatch between source and sink schemas (e.g., missing `timestamp` field).    |

---

## **3. Common Issues and Fixes**

### **Issue 1: Logs/Metrics Vanishing After Archival**
**Root Cause:**
- Archival pipeline failed silently (e.g., dead letter queue not monitored).
- Retention policy deleted data prematurely.
- Sink (e.g., S3, Cassandra) rejected writes.

**Debugging Steps:**
1. **Check Pipeline Metrics**
   Verify if the archival job completed successfully:
   ```bash
   # Example: Check Kafka consumer lag (if using Kafka as intermediary)
   kafka-consumer-groups --bootstrap-server <broker> --group <group> --describe
   ```
   - **Fix:** If lag > 0, scale consumers or adjust partition count.

2. **Validate Sink Integrity**
   Check for write errors in cloud providers (e.g., S3 `PutObject` failures):
   ```bash
   # Example: AWS CLI to list failed uploads
   aws s3api list-object-versions --bucket <bucket> | grep "DELETE_Marker"
   ```
   - **Fix:** Enable **S3 Event Notifications** to alert on failures.

3. **Inspect Retention Policy**
   Ensure the policy isn’t shorter than expected:
   ```yaml
   # Example: Correct ELK retention policy (curator.yml)
   actions:
     1:
       action: delete_indices
       description: "Delete indices older than 90 days"
       filter:
         filtertype: age
         source: name
         direction: older
         unit: days
         unit_count: 90
   ```
   - **Fix:** Extend retention if logs are deleted too soon.

---

### **Issue 2: Storage Costs Spiking**
**Root Cause:**
- Unbounded archival (e.g., no retention on S3 + Glue).
- Duplicate data due to retries or misconfigured deduplication.

**Debugging Steps:**
1. **Audit S3/Cloud Storage Usage**
   Use AWS Cost Explorer to identify unusual growth:
   ```bash
   # Example: List S3 objects with age
   aws s3 ls --summarize --recursive s3://<bucket> | awk '{sum+=$3} END {print sum}'
   ```
   - **Fix:** Apply **S3 Lifecycle Policies** with transition to Infrequent Access (IA) tiers.

2. **Check for Data Duplication**
   Compare log volumes between source (e.g., Fluentd) and sink (e.g., Loki):
   ```go
   // Example: Fluentd plugin to deduplicate (if using Kafka)
   <filter kafka>
     @type record_transformer
     enable_ruby true
     <record>
       deduplicated_at ${record["timestamp"]} # Ensure field exists
     </record>
   </filter>
   ```
   - **Fix:** Add a checksum field (e.g., SHA-256 of log content) and filter duplicates.

---

### **Issue 3: Slow Queries on Archived Data**
**Root Cause:**
- Shard misalignment (e.g., time-based shards not aligned with query ranges).
- Index fragmentation (e.g., Elasticsearch `_force_merge` needed).

**Debugging Steps:**
1. **Inspect Shard Alignment**
   For time-series data, ensure shards are created daily (not hourly):
   ```json
   # Example Elasticsearch index template
   {
     "index_patterns": ["logs-*"],
     "settings": {
       "number_of_shards": 5,
       "index.routing.allocation.total_shards_per_node": 100
     },
     "mappings": {
       "_doc": {
         "dynamic_date_formats": ["yyyy-MM-dd'T'HH:mm:ss.SSSZ"],
         "properties": {
           "@timestamp": { "type": "date" }
         }
       }
     }
   }
   ```
   - **Fix:** Rebuild indices with correct `index.routing.allocation` settings.

2. **Optimize Indexing**
   Run a force merge to reduce segment count:
   ```bash
   # Example: Elasticsearch force merge (run during low-traffic periods)
   curl -X POST "http://localhost:9200/logs-_all/_forcemerge?max_num_segments=1&only_expunge_deletes=true"
   ```
   - **Warning:** Large indices may require manual tuning.

---

### **Issue 4: Failed Archival Jobs (ETL Pipeline)**
**Root Cause:**
- **Source Auth Failure:** API keys expired, IAM policies misconfigured.
- **Sink Quota Exceeded:** AWS S3 PUT limits or Cassandra write quotas hit.
- **Schema Drift:** Source logs missing required fields (e.g., `timestamp`).

**Debugging Steps:**
1. **Check Logs for Errors**
   Inspect Fluentd/Fluent Bit logs:
   ```bash
   journalctl -u fluentd -f --no-pager | grep ERROR
   ```
   - **Fix:** Rotate API keys or adjust IAM policies.

2. **Validate Sink Quotas**
   For Cassandra, check write performance:
   ```cql
   SELECT * FROM system_traces.trace_events
   WHERE trace_id = latest_trace_id();
   ```
   - **Fix:** Upgrade nodes or optimize compaction strategy.

3. **Schema Reconciliation**
   Compare source (e.g., JSON log) and sink (e.g., Parquet) schemas:
   ```python
   # Example: Python script to compare schemas
   import json
   source_schema = json.loads(open("source_schema.json").read())["properties"]
   sink_schema = open("sink_schema.avro").read()  # Use `avro-tools` to inspect
   assert set(source_schema.keys()) == set(sink_schema["fields"])
   ```
   - **Fix:** Add missing fields to the source pipeline.

---

## **4. Debugging Tools and Techniques**
| **Tool**               | **Purpose**                                                                 | **Example Command/Usage**                          |
|------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **Prometheus + Grafana** | Monitor pipeline latency, error rates.                                     | `rate(pipeline_errors_total[1m]) > 0`              |
| **ELK APM**            | Trace slow queries in Elasticsearch.                                        | Enable `slowlog` in `elasticsearch.yml`           |
| **Terraform Cloud**    | Audit infrastructure drift (e.g., S3 bucket policies).                       | `terraform plan`                                   |
| **S3 Object Lock**     | Prevent accidental deletions (WORM compliance).                              | Enable via AWS Console or CLI                     |
| **Fluentd Debug Plugins** | Log pipeline execution details.                                           | Add `<match **> <filter debug>` to Fluentd config  |
| **Kafka Consumer Lag** | Detect backpressure in Kafka-based pipelines.                               | `kafka-consumer-groups --describe`                 |
| **Chaos Engineering**  | Test resilience (e.g., kill archival workers to see failover).               | Use `kubectl delete pod -n observability archival-worker` |

**Pro Tip:**
- **Correlate timestamps** between source (e.g., Fluentd) and sink (e.g., S3) to spot delays.
- **Use distributed tracing** (Jaeger, OpenTelemetry) to trace log entries end-to-end.

---

## **5. Prevention Strategies**
### **1. Infrastructure as Code (IaC)**
- **Apply Terraform/Pulumi** to manage cloud resources (e.g., S3 buckets, IAM roles).
  ```hcl
  # Example: S3 bucket with lifecycle policy
  resource "aws_s3_bucket_lifecycle_configuration" "logs_retention" {
    bucket = aws_s3_bucket.observability_logs.id
    rule {
      id     = "archive-after-90-days"
      status = "Enabled"
      transition {
        days          = 30
        storage_class = "STANDARD_IA"
      }
      expiration {
        days = 90
      }
    }
  }
  ```

### **2. Alerting and Monitoring**
- **Set up alerts** for:
  - S3 PUT errors (`aws_s3_bucket_server_side_encryption_status`).
  - Kafka consumer lag (`kafka_consumer_lag >= threshold`).
  - Elasticsearch cluster health (`elasticsearch_cluster_health <= 90`).
- **Tools:** Prometheus Alertmanager, Datadog, or AWS CloudWatch.

### **3. Idempotency and Deduplication**
- **Use UUIDs or checksums** to avoid duplicates:
  ```javascript
  // Example: Node.js deduplication (Fluent Bit plugin)
  const crypto = require('crypto');
  function getChecksum(log) {
    return crypto.createHash('sha256').update(JSON.stringify(log)).digest('hex');
  }
  ```

### **4. Regular Testing**
- **Chaos Testing:** Randomly kill archival workers to test failover.
- **Data Validation:** Periodically compare source/sink counts (e.g., `COUNT(*)` queries).

### **5. Documentation**
- **Document retention policies** and ownership (e.g., "Team X owns logs-2023").
- **Update schema registry** (e.g., Confluent Avro) when fields change.

---

## **6. Escalation Path**
If issues persist:
1. **Check vendor support** (e.g., Elastic, Datadog, AWS).
2. **Review logs** from all stages (source → processor → sink).
3. **Isolate the failure** (e.g., test with a single log file).
4. **Engage SRE/DevOps** if the problem affects multiple systems.

---
**Final Note:**
Start with **metrics and logs**, not assumptions. The "Change Log Archival" pattern is only as robust as its weakest link—**monitor the pipeline end-to-end**.

Would you like a deep dive on any specific tool (e.g., Fluentd debugging, S3 lifecycle policies)?