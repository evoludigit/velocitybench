# **[Pattern] Hashing Observability Reference Guide**

---

## **Overview**
The **Hashing Observability** pattern ensures consistent and efficient event/metric data deduplication, aggregation, and analysis by applying cryptographic hashing techniques to events or data payloads before processing. This pattern is critical in observability systems where:
- **High cardinality** (e.g., user sessions, API calls) leads to excessive data volume.
- **Exact duplicates** must be eliminated without losing context.
- **Performance** is critical in real-time processing pipelines.

By hashing event identifiers (e.g., correlation IDs, request URIs) or payloads, systems can:
✔ **Deduplicate** events efficiently (e.g., avoid reprocessing duplicate logs).
✔ **Aggregate metrics** at a granular level (e.g., count requests per hashed URI).
✔ **Optimize storage** by storing only unique hashes.
✔ **Preserve privacy** by anonymizing raw data via irreversible hashing.

This guide covers schema design, implementation strategies, query patterns, and related observability techniques.

---

## **1. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 | **Example Use Case**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Hash Function**      | Cryptographic algorithm (e.g., SHA-256, MurmurHash) that maps input to a fixed-size hash value. Collision-resistant for uniqueness.                                                                    | Hashing user session IDs to deduplicate tracking events.                                               |
| **Deterministic Hashing** | Same input → same hash output (critical for deduplication).                                                                                                                                                 | Hashing API endpoint paths to group identical requests.                                                  |
| **Hash Collision**     | Rare but possible scenario where two different inputs produce the same hash. Mitigated via robust algorithms (e.g., SHA-3).                                                                         | Minimal risk; use 256-bit hashes for observability.                                                        |
| **Salting**            | Adding random data to input before hashing to prevent rainbow table attacks (less common in observability but useful for sensitive data).                                                               | Not typically needed; focus on uniqueness over security.                                                 |
| **Hash Key**           | The hashed output stored/queried in observability systems (e.g., `sha256(user_id)`).                                                                                                                       | Querying metrics by `hash_key` instead of raw `user_id`.                                                 |
| **Payload Hashing**    | Hashing entire event payloads (not just IDs) to detect structural duplicates across systems.                                                                                                             | Deduplicating error logs with identical payloads but different `event_id`s.                             |
| **Bloom Filter**       | Probabilistic data structure to pre-check hash membership (reduces storage queries).                                                                                                                      | Fastly checking if a hash exists before writing to a database.                                          |

---

## **2. Schema Reference**

### **2.1 Core Tables/Collections**
| **Field**             | **Type**       | **Description**                                                                                                                                                         | **Example Value**                     |
|-----------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `event_id`            | `STRING`       | Unique identifier for the original event (optional; retained for debugging).                                                                                           | `"req_456789"`                         |
| `hash_key`            | `STRING`       | Cryptographic hash of the event (e.g., `SHA256(event_id || payload)`).                                                                                              | `"a1b2c3..."` (truncated for brevity) |
| `original_payload`    | `JSON`/`TEXT`  | Original event data (hashed for storage; may be redacted).                                                                                                          | `{"user_id": "123", "uri": "/login"}` |
| `hash_type`           | `STRING`       | Algorithm used (e.g., `SHA256`, `MurmurHash3_128`).                                                                                                                   | `"SHA256"`                             |
| `timestamp`           | `TIMESTAMP`    | Event ingestion time (for deduplication timewindows).                                                                                                                 | `2024-03-15T14:30:00Z`                 |
| `metadata`            | `JSON`         | Additional context (e.g., `source_system`, `dedup_window_sec`).                                                                                                      | `{"source": "api_gateway", "window": 300}` |

---

### **2.2 Example Schema (SQL/NoSQL)**
#### **Relational (PostgreSQL)**
```sql
CREATE TABLE hashed_events (
    event_id VARCHAR(64),
    hash_key VARCHAR(64) PRIMARY KEY,
    original_payload JSONB,
    hash_type VARCHAR(32),
    timestamp TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);
```

#### **Document (MongoDB)**
```json
{
  "_id": ObjectId("..."),
  "event_id": "req_456789",
  "hash_key": "a1b2c3...",
  "original_payload": {"user_id": "123", "uri": "/login"},
  "hash_type": "SHA256",
  "timestamp": ISODate("2024-03-15T14:30:00Z"),
  "metadata": {"source": "api_gateway", "window": 300}
}
```

#### **Time-Series (InfluxDB)**
```sql
CREATE RETENTION POLICY hashed_observability
  DURATION 30d
  REPLICATION 1
  DEFAULT
ON "events"
```

```sql
-- Create hash-keyed series
CREATE CONTINUOUS QUERY dedup_events
RETENTION 30d
ON events
SELECT mean("count") AS unique_events
WHERE hash_key = 'a1b2c3...'
GROUP BY time(5m)
```

---

## **3. Implementation Strategies**

### **3.1 Hashing Strategies**
| **Strategy**               | **Use Case**                                                                                                                                                                                                 | **Example**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **ID Hashing**             | Deduplicate events by unique IDs (e.g., `user_id`, `request_id`).                                                                                                                                      | `hash_key = SHA256("user_123")`                                                                |
| **Payload Hashing**        | Deduplicate events with identical content (even if IDs differ).                                                                                                                                           | `hash_key = BLAKE3(JSON.stringify(payload))`                                                  |
| **Composite Hashing**      | Combine multiple fields (e.g., `user_id + endpoint + action`) for granularity.                                                                                                                        | `hash_key = SHA256("user_123||/api/login||POST")`                                            |
| **Bloom Filter Pre-Check** | Avoid writing duplicates to storage by checking hashes first.                                                                                                                                              | Use `Redis` Bloom filter to check `EXISTS hash_key` before inserting.                          |
| **Local vs. Distributed**  | Local hashing (e.g., in-memory) for speed; distributed hashing (e.g., `SHA256`) for consistency across systems.                                                                                          | Local: `MurmurHash3` for quick deduplication; Distributed: `SHA3_256` for cross-system sync.   |

---

### **3.2 Deduplication Windows**
| **Window Type**       | **Definition**                                                                                                                                                                                                 | **Query Example (SQL)**                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Sliding Window**    | Delete hashes older than `X` seconds (e.g., 5-minute window).                                                                                                                                          | `DELETE FROM hashed_events WHERE timestamp < NOW() - INTERVAL '5 minutes'`                     |
| **Fixed Window**      | Group hashes by time buckets (e.g., per hour).                                                                                                                                                            | `SELECT hash_key, COUNT(*) FROM hashed_events GROUP BY DATE_TRUNC('hour', timestamp)`      |
| **Tumbling Window**   | Non-overlapping buckets (e.g., 10 AM–11 AM slot).                                                                                                                                                         | `CREATE TABLE hourly_hashes AS SELECT * FROM hashed_events WHERE timestamp BETWEEN '2024-03-15 10:00' AND '2024-03-15 11:00'` |

---

## **4. Query Examples**

### **4.1 Basic Deduplication Queries**
#### **Check for Duplicate Hashes (SQL)**
```sql
-- Count unique users by hashed ID
SELECT hash_key, COUNT(*) AS event_count
FROM hashed_events
WHERE hash_type = 'SHA256'
GROUP BY hash_key
HAVING COUNT(*) > 1;
```

#### **Filter by Time Window (MongoDB)**
```javascript
// Find hashes from the last 5 minutes
db.hashed_events.find({
  timestamp: { $gte: new Date(Date.now() - 5 * 60 * 1000) },
  hash_type: "SHA256"
});
```

---

### **4.2 Aggregation Queries**
#### **Unique Requests per Endpoint (InfluxDB)**
```sql
-- Count unique `/login` requests by hash_key
SELECT
    COUNT_DISTINCT("hash_key") AS unique_logins
FROM "events"
WHERE "uri" = '/login'
GROUP BY time(1h)
```

#### **Anomaly Detection (SQL)**
```sql
-- Flag hashes with unusually high volume
WITH hash_counts AS (
  SELECT
    hash_key,
    COUNT(*) AS frequency,
    PERCENTILE_CONT(0.95) OVER () AS p95_threshold
  FROM hashed_events
  GROUP BY hash_key
)
SELECT hash_key
FROM hash_counts
WHERE frequency > p95_threshold;
```

---

### **4.3 Payload Hashing (Advanced)**
#### **Find Duplicate Error Payloads (Python Example)**
```python
import hashlib
from collections import defaultdict

payloads = [
    {"error": "timeout", "code": 504},
    {"error": "timeout", "code": 504},  # Duplicate
    {"error": "not_found", "code": 404}
]

hash_map = defaultdict(list)
for payload in payloads:
    payload_str = json.dumps(payload, sort_keys=True)
    hash_key = hashlib.sha256(payload_str.encode()).hexdigest()
    hash_map[hash_key].append(payload)

# Output duplicates
for key, duplicates in hash_map.items():
    if len(duplicates) > 1:
        print(f"Duplicate payload hash: {key}, Duplicates: {len(duplicates)}")
```

---

## **5. Performance Considerations**
| **Optimization**               | **Impact**                                                                                                                                                                                                 | **Tools/Techniques**                                                                             |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Hash Collision Handling**     | Minimize false positives with larger hash sizes (e.g., 256-bit).                                                                                                                                         | Use `SHA3_256` instead of `MD5`.                                                               |
| **Indexing**                    | Index `hash_key` and `timestamp` for fast lookups.                                                                                                                                                       | PostgreSQL: `CREATE INDEX idx_hashes ON hashed_events(hash_key, timestamp)`                   |
| **Batch Processing**            | Hash in parallel (e.g., spark jobs) to scale.                                                                                                                                                           | Apache Spark: `DataFrame.hash("event_id")`                                                    |
| **Memory Efficiency**           | Use Bloom filters to avoid disk I/O for duplicate checks.                                                                                                                                               | Redis: `BF.ADD myfilter hash_key`                                                              |
| **Truncation**                  | Store only first `N` bytes of hash (e.g., 16 bytes for `SHA256`) if collisions are negligible.                                                                                                      | `hash_key = hash_key[:16]`                                                                     |

---

## **6. Related Patterns**
| **Pattern**                  | **Relation to Hashing Observability**                                                                                                                                                                      | **When to Use Together**                                                                          |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Sampling**                 | Combine hashing with probabilistic sampling to reduce volume further (e.g., hash + `SIMPLE` sampling).                                                                                            | High-volume systems (e.g., 1M+ events/sec) where full deduplication is costly.                   |
| **Data Sketching**           | Use sketches (e.g., HyperLogLog) to estimate unique hashes without storing them.                                                                                                                       | Approximate unique count queries (e.g., "How many unique users?").                              |
| **Event Routing**             | Route events to specific observability systems based on hash prefixes (e.g., `hash_key[0:2]` → `log_cluster_1`).                                                                                   | Distributed systems with multiple observability backends.                                        |
| **Anomaly Detection**         | Hash-based deduplication feeds into anomaly detection (e.g., unexpected spikes in `hash_key` frequencies).                                                                                         | Detecting bot traffic or DDoS via unusual hash patterns.                                        |
| **Data Retention Policies**   | Hashing + TTL (Time-to-Live) policies to automatically purge old deduplicated data.                                                                                                                   | Cost-sensitive environments (e.g., cloud observability).                                        |

---

## **7. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                                                                                                                                                 | **Mitigation**                                                                                     |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Non-Deterministic Hashing**   | Using `UUID.v4()` or random hashes leads to inconsistent deduplication.                                                                                                                               | Always use deterministic algorithms (e.g., `SHA256(input)`).                                   |
| **Ignoring Collisions**         | Assuming no collisions in low-cardinality systems can fail with high-volume data.                                                                                                                   | Test with `N` = 10,000,000 inputs to verify collision rate (should be < 0.0001%).                 |
| **Over-Hashing**                | Hashing every field in a payload can create "salted" hashes that break expected deduplication.                                                                                                      | Hash only critical fields (e.g., `user_id + action`).                                          |
| **Hardcoding Hash Algorithms**  | Storing `hash_type` as a static column prevents future algorithm upgrades.                                                                                                                       | Make `hash_type` a field and support migrations (e.g., prepend algorithm name to hash).       |
| **No Time Windows**             | Storing all hashes indefinitely bloats storage.                                                                                                                                                   | Implement sliding/windowed retention policies.                                                  |

---

## **8. Tools & Libraries**
| **Category**               | **Tools**                                                                                                                                                                                                 | **Use Case**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Hashing Libraries**      | Python: `hashlib`, `blake3`; Go: `crypto/sha256`; Java: `MessageDigest`.                                                                                                                               | Generating `hash_key` in ingestion pipelines.                                                   |
| **Deduplication Engines**  | Kafka: [`DeserializationFilter`](https://kafka.apache.org/documentation/#dedupe); Flink: `KeyedStream` with hashing.                                                                                   | Stream processing deduplication.                                                               |
| **Storage Engines**        | PostgreSQL: `pg_trgm` for fuzzy matching; ClickHouse: `hash()` function.                                                                                                                              | Efficient storage and querying of hashed data.                                                   |
| **Bloom Filters**          | Redis: `BF` module; Apache Spark: `BloomFilter`.                                                                                                                                                   | Pre-filtering hashes before ingestion.                                                         |
| **Sampling + Hashing**     | Google’s [`Turing`](https://github.com/google/turing); AWS Kinesis Data Analytics.                                                                                                                 | Scalable approximate deduplication.                                                            |

---

## **9. Example Workflow**
1. **Ingestion**:
   - API gateway receives 10,000 `/login` requests in 1 minute.
   - Each request has a `user_id` and `payload`.
   - Compute `hash_key = SHA256(user_id || "/login")`.

2. **Deduplication**:
   - Check Redis Bloom filter: `BF.MIGHT_HAVE hash_key` → Not found.
   - Insert into database: `INSERT INTO hashed_events (hash_key, timestamp) VALUES (..., NOW())`.
   - Add to Bloom filter: `BF.ADD myfilter hash_key`.

3. **Aggregation**:
   - Query unique logins: `SELECT COUNT(DISTINCT hash_key) FROM hashed_events WHERE uri = '/login'`.

4. **Retention**:
   - Delete hashes older than 7 days: `DELETE FROM hashed_events WHERE timestamp < NOW() - INTERVAL '7 days'`.

---
**Total Unique Logins**: 5,200 (out of 10,000 raw events).