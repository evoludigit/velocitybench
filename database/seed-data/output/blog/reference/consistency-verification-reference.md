# **[Pattern] Consistency Verification Reference Guide**

---

## **Overview**
The **Consistency Verification** pattern ensures data integrity across distributed systems by validating that replicated or propagated data remains accurate and uniform. It is critical in systems where multiple services or databases store related data, requiring checks to detect inconsistencies caused by network delays, partial failures, or conflicting updates.

This pattern applies to:
- **Eventual consistency models** (e.g., DynamoDB, Cassandra)
- **Microservices architectures** with decoupled data stores
- **Multi-master replication** scenarios
- **Hybrid transactional/analytical processing (HTAP)**

The pattern prevents silent failures by detecting discrepancies and triggering corrective actions, such as retries, rollbacks, or manual intervention. It is distinct from consensus algorithms (e.g., Paxos, Raft) because it focuses on post-facto verification rather than preventing divergence.

---

## **Key Concepts**

| **Concept**               | **Definition**                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consistency Check**     | A mechanism to compare data states across replicas or services. Examples: *row-by-row comparison*, *summary statistics*, or *transactional integrity checks*.                                                                                                                                                                                                                                   |
| **Tolerance Threshold**   | Acceptable divergence before an inconsistency is flagged as critical. Example: A tolerance of *0.1% divergence rate* in key-value stores.                                                                                                                                                                                                                                                 |
| **Verification Interval** | Frequency of running consistency checks. Balances resource overhead vs. latency tolerance. Example: *Hourly full syncs* or *real-time triggers on write operations*.                                                                                                                                                                                                                                  |
| **Collision Resolution**  | Strategy for handling conflicting updates. Options: *Last-write-wins (LWW)*, *manual override*, or *custom merge logic*.                                                                                                                                                                                                                                                                                            |
| **Audit Log**             | A traceable record of detected inconsistencies, their timestamps, and resolution status. Supports debugging and compliance.                                                                                                                                                                                                                                                                          |
| **Quorum Checks**         | Requiring a majority of replicas to agree on a value before declaring consistency. Example: *3/5 replicas must match for a critical update*.                                                                                                                                                                                                                                                   |

---

## **Implementation Schema**

| **Schema Field**         | **Type**       | **Description**                                                                                                                                                                                                                                                                                                                                                                                                                          | **Example Values**                     |
|--------------------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| **Check Type**           | Enum           | Defines the method of verification: *full sync, diff-based, probabilistic sampling, or checksum validation*.                                                                                                                                                                                                                                                                                                                       | `full_sync`, `diff_based`, `checksum`  |
| **Scope**                | Enum           | Defines the data scope: *replica-level, cluster-level, or service-level*.                                                                                                                                                                                                                                                                                                                                                           | `replica`, `cluster`, `service`        |
| **Tolerance**            | Float          | Maximum allowed divergence (e.g., 0.5% for low-latency systems).                                                                                                                                                                                                                                                                                                                                                                    | `0.005`                                  |
| **Verification Interval**| Duration       | How often checks are run (e.g., `PT1M` for synchronous systems).                                                                                                                                                                                                                                                                                                                                                              | `PT1H`, `PT5M`                           |
| **Collision Strategy**   | Enum           | How to resolve conflicting writes.                                                                                                                                                                                                                                                                                                                                                                                                       | `lww`, `manual`, `merge`               |
| **Audit Enabled**        | Boolean        | Whether to log discrepancies.                                                                                                                                                                                                                                                                                                                                                                                                         | `true`/`false`                           |
| **Quorum Threshold**     | Integer        | Minimum number of agreeing replicas for consistency.                                                                                                                                                                                                                                                                                                                                                                            | `3/5`                                    |
| **Trigger Event**        | Enum           | What triggers verification: *write operation, timer-based, or manual*.                                                                                                                                                                                                                                                                                                                                                                               | `write`, `timer`, `manual`              |

---

## **Query Examples**

### **1. Query for Full Replica Consistency Check**
```sql
-- SQL (PostgreSQL) example: Compare two replicas' data tables.
SELECT
    COUNT(*) AS inconsistent_records,
    SUM(CASE WHEN r1.data != r2.data THEN 1 ELSE 0 END) AS divergence_count
FROM replica1.r1 JOIN replica2.r2 ON r1.id = r2.id
WHERE r1.data != r2.data;
```

**Output Interpretation:**
- `inconsistent_records = 0`: No discrepancies.
- `divergence_count > 0`: Query a `collision_resolution` strategy.

---

### **2. Probabilistic Sampling Check (for Large Datasets)**
```python
# Python example using `great-expectations` for sampling.
import great_expectations as ge

sampler = ge.dataframe_sampler.DataFrameSampler(sample_df)
expectation = sampler.expect_column_values_to_match_regex(
    column="user_id",
    regex=r"^[A-Za-z0-9]{8}$"
)
if not expectation.success:
    trigger_alert("Sampling inconsistency detected")
```

---

### **3. Checksum Validation (for High Throughput)**
```bash
# Bash example: Compare checksums of replicated files.
diff <(md5sum replica1/data.csv) <(md5sum replica2/data.csv)
if [ $? -ne 0 ]; then
    echo "Checksum mismatch!" | send_alert
fi
```

---

### **4. Event-Based Trigger (e.g., After a Write)**
```typescript
// Node.js example: Trigger verification on write completion.
app.post('/update', async (req, res) => {
    await db.write(req.body);
    await consistency.verify("transactional_write"); // Calls a consistency consumer
    res.status(200).send("Updated and verified");
});
```

---

## **Best Practices**
1. **Start Small**: Begin with low-frequency, sample-based checks before scaling to full syncs.
2. **Choose Tolerances Wisely**: Set thresholds based on application SLOs (e.g., 99.9% consistency).
3. **Prioritize Critical Data**: Use quorum checks for high-impact tables (e.g., inventory, user profiles).
4. **Log Collisions**: Maintain a detailed audit trail for debugging (e.g., `discrepancy_id`, `resolved_by`).
5. **Automate Resolutions**: Use LWW or merge logic for non-critical data; flag manual reviews for critical fields.

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Use Case**                                                                                                                                                                                                                                                                                                                                                                                                                         |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Saga Pattern**                | Manages distributed transactions by orchestrating compensating actions.                                                                                                                                                                                                                                                                                                                                                                       | When transactions span multiple services requiring rollback capabilities.                                                                                                                                                                                                                                                                                                                                                                                       |
| **Event Sourcing**              | Stores data as a sequence of immutable events.                                                                                                                                                                                                                                                                                                                                                                                             | Applications requiring precise audit trails (e.g., financial ledgers).                                                                                                                                                                                                                                                                                                                                                                 |
| **Idempotency Keys**             | Ensures retries or duplicate operations don’t cause side effects.                                                                                                                                                                                                                                                                                                                                                             | APIs handling user uploads or payment processing.                                                                                                                                                                                                                                                                                                                                                                             |
| **CAP Theorem Tradeoffs**        | Balances consistency (C), availability (A), and partition tolerance (P).                                                                                                                                                                                                                                                                                                                                                               | Choosing between strong consistency (CP) or availability (AP).                                                                                                                                                                                                                                                                                                                                                                           |
| **Conflict-Free Replicated Data Types (CRDTs)** | Data structures that converge asynchronously.                                                                                                                                                                                                                                                                                                                                                                                       | Collaborative editing tools (e.g., Google Docs).                                                                                                                                                                                                                                                                                                                                                                           |

---

## **Failure Modes & Mitigations**

| **Failure Mode**               | **Description**                                                                                                                                                                                                                                                                                                                                                                                                                     | **Mitigation**                                                                                                                                                                                                                                                                                                                                                                                                                     |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **False Negatives**             | Checks miss actual inconsistencies.                                                                                                                                                                                                                                                                                                                                                                                   | Increase sample size or switch to full syncs.                                                                                                                                                                                                                                                                                                                                                                                   |
| **Check Overhead**              | Verification slows down write operations.                                                                                                                                                                                                                                                                                                                                                                                 | Use probabilistic sampling or background threads.                                                                                                                                                                                                                                                                                                                                                                                   |
| **Collision Escalation**        | Manual review is required for all conflicts.                                                                                                                                                                                                                                                                                                                                                                                   | Implement merge logic for non-critical fields.                                                                                                                                                                                                                                                                                                                                                                                   |
| **Data Drift**                  | Gradual divergence over time.                                                                                                                                                                                                                                                                                                                                                                                   | Schedule periodic full syncs or use checksums.                                                                                                                                                                                                                                                                                                                                                                                   |
| **Alert Fatigue**               | Too many false alarms.                                                                                                                                                                                                                                                                                                                                                                                   | Set adaptive thresholds or implement confidence scoring.                                                                                                                                                                                                                                                                                                                                                                                   |

---
**Note**: For production use, combine this pattern with **retries, circuit breakers, and chaos engineering** to handle edge cases.