# **[Pattern] Deduplication Patterns Reference Guide**

---

## **Overview**
Deduplication Patterns provide structured approaches to eliminate duplicate data entries across databases, applications, or data pipelines. Duplicates can arise from system errors, user inputs, or integration mismatches, leading to inefficiencies, inconsistent reporting, and degraded system performance. This reference guide outlines common **deduplication patterns**—standardized strategies for identifying, resolving, or preventing duplicate records. Implementations cover **client-side**, **server-side**, and **pipeline-based** deduplication, with focus on scalability, cost-efficiency, and accuracy.

---

## **Key Concepts**
Deduplication typically follows a four-phase workflow:
1. **Detection**: Identifying potential duplicates via similarity checks or unique identifiers.
2. **Resolution**: Deciding whether to keep, merge, or discard records.
3. **Prevention**: Applying constraints to avoid future duplicates.
4. **Monitoring**: Tracking deduplication effectiveness and updating rules.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                     | **Example Fields**                                  |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Duplicate Key**           | Unique identifier (e.g., composite key) to detect exact matches.                                   | `user_id`, `email`, `(name + address)`              |
| **Fuzzy Matching Rule**     | Algorithms/thresholds for partial similarity (e.g., Levenshtein distance for names).               | `name_similarity_threshold=0.85`                    |
| **Deduplication Trigger**   | Event or condition (e.g., insert/update event, batch job) triggering deduplication logic.          | `on_insert`, `on_batch_process`                    |
| **Resolution Strategy**     | Rules for handling duplicates (e.g., keep newest, merge fields, discard).                          | `keep_newest`, `merge_fields=firstName,lastName`   |
| **Audit Log**               | Track deduplication actions (success/failure, decisions made) for compliance/reporting.            | `action_time`, `record_id`, `decision`             |

---

## **Implementation Details**

### **1. Client-Side Deduplication**
**Use Case**: Frontend validation before data submission (e.g., form entries).
**When to Use**: Low-volume, real-time validation (e.g., user registrations).
**Implementation**:
- Use **local caches** (e.g., IndexedDB for browsers) to store recent submissions.
- Apply **hashing** (e.g., SHA-1) on critical fields (e.g., `email`) for quick comparison.
- **Trigger**: Validate on `submit` or `blur` events.

**Example (JavaScript)**:
```javascript
// Cache submissions via email hashes
const submissionCache = new Set();

document.querySelector('form').addEventListener('submit', (e) => {
  const email = e.target.email.value;
  const emailHash = crypto.subtle.digest('SHA-1', new TextEncoder().encode(email)).then(hash => {
    if (submissionCache.has(hash)) {
      alert('Duplicate email detected!');
      e.preventDefault();
    } else {
      submissionCache.add(hash);
      e.target.submit();
    }
  });
});
```

**Pros**:
- Low-latency feedback.
- Reduces server load.

**Cons**:
- No guarantee of global uniqueness.
- Client-side only; vulnerable to spoofing.

---

### **2. Server-Side Deduplication**
**Use Case**: Database-level enforcement (e.g., unique constraints, triggers).
**When to Use**: Critical data (e.g., financial records, user accounts) requiring strict uniqueness.
**Implementation**:
- **Database Constraints**:
  ```sql
  -- PostgreSQL: Exact match on email
  CREATE UNIQUE INDEX unique_email ON users (email);

  -- MySQL: Composite unique key
  ALTER TABLE orders ADD UNIQUE (customer_id, order_date);
  ```
- **Application Logic**:
  Use ORM methods to check duplicates before writes:
  ```python
  # Django: Prevent duplicate accounts
  if User.objects.filter(email=email).exists():
      raise ValueError("Email already registered.")
  ```

- **Triggers** (e.g., PostgreSQL):
  ```sql
  CREATE OR REPLACE FUNCTION check_duplicate_name()
  RETURNS TRIGGER AS $$
  BEGIN
    IF EXISTS (
      SELECT 1 FROM customers
      WHERE name = NEW.name AND id != NEW.id
    ) THEN
      RAISE EXCEPTION 'Duplicate name detected';
    END IF;
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trig_check_name
  BEFORE INSERT OR UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION check_duplicate_name();
  ```

**Pros**:
- Enforced at the database level.
- Supports complex rules (e.g., partial matches).

**Cons**:
- Higher latency for partial/fuzzy matching.
- Requires schema changes.

---

### **3. Pipeline-Based Deduplication**
**Use Case**: Large-scale data processing (e.g., ETL, logs, IoT streams).
**When to Use**: Batch processing or streaming data (e.g., Kafka, Spark).
**Implementation**:
- **Apache Spark**:
  ```scala
  // Deduplicate RDD by a key
  val dedupedRDD = rdd.keyBy(_.id).reduceByKey((a, b) => a).map(_._2)
  ```
- **Kafka Streams**:
  ```java
  // Remove duplicates via windowed aggregation
  StreamsBuilder builder = new StreamsBuilder();
  builder.stream("input-topic")
         .groupByKey()
         .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
         .aggregate(
           (key, value) -> value,
           (aggKey, newValue) -> newValue // Keep latest
         );
  ```
- **Custom ETL Scripts**:
  Use **bloom filters** for probabilistic deduplication in memory:
  ```python
  from pybloom_live import ScalableBloomFilter

  bloom = ScalableBloomFilter(initial_capacity=1000000, error_rate=0.01)
  for record in stream:
      key = hash(record['email'])
      if bloom.check(key):
          continue  # Skip duplicate
      bloom.add(key)
      process(record)
  ```

**Pros**:
- Scalable for big data.
- Supports real-time streaming.

**Cons**:
- Higher computational overhead.
- Requires infrastructure (e.g., Spark cluster).

---

### **4. Hybrid Deduplication**
Combine client-side, server-side, and pipeline approaches for robustness:
1. **Client**: Validate on submission.
2. **Server**: Enforce constraints + log potential collisions.
3. **Pipeline**: Resolve conflicts in batch jobs.

**Example Workflow**:
```
User → Submits Form → Client checks cache → Server validates → Database rejects → Log to pipeline → Resolve in nightly job.
```

---

## **Query Examples**

### **Exact Deduplication (SQL)**
```sql
-- Find exact duplicates by composite key
SELECT * FROM orders
WHERE (customer_id, order_date) IN (
  SELECT customer_id, order_date
  FROM orders
  GROUP BY customer_id, order_date
  HAVING COUNT(*) > 1
);
```

### **Fuzzy Deduplication (Python with `fuzzywuzzy`)**
```python
from fuzzywuzzy import fuzz

def find_similar_names(names, threshold=80):
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            if fuzz.ratio(name1, name2) > threshold:
                yield (name1, name2)

# Usage:
names = ["John Doe", "Jon Doe", "Jane Doe"]
for match in find_similar_names(names):
    print(f"Similar: {match}")
```

### **Time-Based Deduplication**
```sql
-- Mark duplicates within 5 minutes of each other
WITH time_windows AS (
  SELECT
    user_id,
    event_time,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_time) AS rn
  FROM events
)
DELETE FROM events
WHERE rn > 1 AND event_time > (
  SELECT MAX(event_time) - INTERVAL '5 minutes'
  FROM events
  WHERE user_id = time_windows.user_id
  AND event_time <= time_windows.event_time
);
```

---

## **Performance Considerations**
| **Pattern**               | **Time Complexity**       | **Space Complexity**       | **Best For**                  |
|---------------------------|---------------------------|----------------------------|--------------------------------|
| Exact Match (Hash)        | O(1)                      | O(n)                       | Database constraints           |
| Fuzzy Matching (Levenshtein)| O(n*m)                  | O(n)                       | Partial similarity checks      |
| Bloom Filter              | O(1)                      | O(m)                       | Streaming/data pipelines       |
| Triggers/Stored Procedures| Depends on DB             | Depends on DB               | Real-time validation           |

---

## **Related Patterns**
1. **[Idempotency Pattern](insert-link)**
   - Ensures operations (e.g., API calls) are repeatable without side effects, complementing deduplication.
2. **[Event Sourcing](insert-link)**
   - Logs state changes as immutable events, simplifying duplicate resolution in audit trails.
3. **[Sharding](insert-link)**
   - Distributes data to reduce collision probability in large-scale systems.
4. **[Data Masking](insert-link)**
   - Protects sensitive fields (e.g., SSN) during deduplication comparisons.
5. **[Circuit Breaker](insert-link)**
   - Prevents cascading failures in systems where deduplication services may throttle.

---
## **Troubleshooting**
| **Issue**                     | **Cause**                          | **Solution**                                  |
|--------------------------------|------------------------------------|-----------------------------------------------|
| False Positives in Fuzzy Match | Low threshold                      | Increase similarity threshold or adjust algorithm. |
| High Latency in Pipeline      | Inefficient joins/aggregations     | Use approximate algorithms (e.g., MinHash).   |
| Database Lock Contention       | Heavy trigger usage                | Offload to application layer or batch jobs.   |
| Client-Side Spoofing           | Bypassing validation               | Combine with server-side checks.              |

---
## **Best Practices**
1. **Define Uniqueness Early**: Design schemas with uniqueness constraints in mind (e.g., composite keys).
2. **Prioritize Performance**: Use hashing for exact matches; fuzzy methods for partial matches.
3. **Log Decisions**: Maintain an audit trail for compliance (e.g., GDPR).
4. **Monitor Collisions**: Track deduplication failures to refine rules.
5. **Test Edge Cases**: Include typos, international characters, and null values in tests.