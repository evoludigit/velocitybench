# **Debugging Keyset Pagination: A Troubleshooting Guide**

## **Introduction**
Keyset pagination (also called cursor-based pagination) is a high-performance alternative to traditional offset-based pagination. It avoids the inefficiency of `LIMIT-OFFSET` queries by fetching records based on a previously returned key (e.g., an ID, timestamp, or hash). While efficient, it can encounter pitfalls like missing keys, invalid cursors, or performance degradation under load.

This guide provides a structured approach to diagnosing and resolving issues with keyset pagination.

---

## **1. Symptom Checklist**
Check for these signs when debugging keyset pagination issues:

### **Client-Side Symptoms**
- [ ] Pagination "breaks" after a few requests (e.g., `nextPageCursor` is missing or invalid).
- [ ] Empty responses despite valid cursors.
- [ ] Duplicate or missing records in pagination results.
- [ ] High API latency during pagination, especially after many pages.
- [ ] Cursors expiring or becoming stale (e.g., due to concurrent writes).

### **Server-Side Symptoms**
- [ ] Database queries with `WHERE key > cursor` return unexpected results.
- [ ] Missing `ORDER BY` or improper indexing on the cursor column.
- [ ] High CPU/memory usage due to inefficient cursor handling.
- [ ] Timeouts or slow responses when fetching large datasets.
- [ ] Race conditions where cursors become invalid after concurrent updates.

### **Database-Specific Symptoms**
- [ ] Index scans instead of index seeks on the cursor column.
- [ ] Temporary tables or cursors stored inefficiently (e.g., in-memory).
- [ ] Unhandled edge cases (e.g., `NULL` cursors, duplicate keys).

---

## **2. Common Issues and Fixes**

### **Issue 1: Missing or Invalid Cursors**
**Symptoms:**
- `nextPageCursor` is `null` or invalid (e.g., incorrect type, malformed).
- API returns `400 Bad Request` for invalid cursors.

**Root Causes:**
- The cursor column is not properly generated (e.g., missing `ORDER BY`).
- The cursor format is incorrect (e.g., stringified JSON vs. integer ID).
- No fallback logic for the first page (e.g., returning `NULL` instead of a min/max value).

**Fixes:**

#### **A. Ensure Proper `ORDER BY`**
Always include an `ORDER BY` clause on the cursor column to guarantee deterministic results.

**Example (PostgreSQL, MySQL, SQL Server):**
```sql
-- Correct: Return the LAST cursor for the next page
SELECT id, data FROM users
WHERE id > :lastCursor
ORDER BY id ASC
LIMIT 20;
```

**Bad (missing `ORDER BY`):**
```sql
-- Missing ORDER BY causes undefined ordering!
SELECT id FROM users WHERE id > :cursor;
```

#### **B. Generate a Proper Cursor**
The cursor should uniquely identify a row and allow fetching the next set.

**Example: Using UUIDs (recommended for distributed systems)**
```python
# Generate a cursor as a hex string
next_page_cursor = hashlib.sha256(str(newest_record.id).encode()).hexdigest()
```

**Example: Using a Timestamp + ID (simpler, but less unique)**
```python
next_page_cursor = f"{record.created_at}_{record.id}"
```

#### **C. Handle the First Page Gracefully**
For the first request, provide a starting cursor (e.g., `NULL` or the smallest possible value).

**Example (SQL):**
```sql
-- First page: Fetch records where cursor IS NULL (or min possible value)
SELECT * FROM users
WHERE id > (SELECT MIN(id) FROM users)
ORDER BY id ASC
LIMIT 20;
```

**Fix in Python (Flask/FastAPI):**
```python
def get_paginated_data(cursor=None):
    if cursor is None:
        cursor = "0"  # or the smallest ID in the table
    query = "SELECT * FROM users WHERE id > %s ORDER BY id ASC LIMIT 20"
    return db.execute(query, (cursor,))
```

---

### **Issue 2: Performance Degradation with Large Datasets**
**Symptoms:**
- Slow responses for deep pagination (e.g., 100+ pages).
- Database queries become inefficient (e.g., full table scans).

**Root Causes:**
- Missing indexes on the cursor column.
- Inefficient cursor storage (e.g., large strings in JSON).
- No caching of frequently accessed cursors.

**Fixes:**

#### **A. Optimize Database Indexes**
Ensure the cursor column is indexed.

**Example (PostgreSQL):**
```sql
CREATE INDEX idx_users_id ON users(id);
```

**Example (MongoDB):**
```javascript
db.users.createIndex({ id: 1 });
```

#### **B. Use Efficient Cursor Formats**
Avoid large strings (e.g., UUIDs) if integers or timestamps suffice.

**Bad (slow due to string comparison):**
```python
cursor = str(uuid.uuid4())  # 32-byte string
```

**Better (fast with integers):**
```python
cursor = newest_record.id  # integer
```

#### **C. Implement Cursor Caching**
Cache frequently used cursors (e.g., in Redis) to avoid repeated DB lookups.

**Example (Redis Cache):**
```python
import redis
r = redis.Redis()

def get_cached_cursor(cursor):
    return r.get(f"cursor:{cursor}")
```

---

### **Issue 3: Race Conditions with Concurrent Writes**
**Symptoms:**
- Cursors become invalid due to concurrent inserts/deletes.
- Missing or duplicate records after pagination.

**Root Causes:**
- No transaction isolation during cursor generation.
- Optimistic locking not applied to cursor values.

**Fixes:**

#### **A. Use Transactions for Cursor Generation**
Ensure atomicity when fetching and updating cursors.

**Example (PostgreSQL):**
```sql
BEGIN;
-- Fetch data for pagination
SELECT * FROM users WHERE id > :cursor ORDER BY id ASC LIMIT 20;

-- If modifying data, ensure consistency
UPDATE users SET status = 'active' WHERE id = :new_id;

COMMIT;
```

#### **B. Use Pessimistic Locking (if needed)**
Lock the cursor range to prevent concurrent modifications.

**Example (PostgreSQL):**
```sql
-- Lock rows to prevent concurrent updates
SELECT id FROM users
WHERE id > :cursor
ORDER BY id ASC
FOR UPDATE;
```

#### **C. Handle Concurrent Deletes Gracefully**
If records can be deleted, ensure cursors remain valid.

**Example (MySQL):**
```sql
-- Soft delete: Mark records as deleted instead of removing them
DELETE FROM users WHERE id = :deleted_id AND deleted_at IS NULL;
```

---

### **Issue 4: Cursors Expire or Become Stale**
**Symptoms:**
- Old cursors return incorrect or missing data.
- API returns "cursor expired" errors.

**Root Causes:**
- No TTL (time-to-live) mechanism for cursors.
- Concurrent updates modify data beneath a cursor.

**Fixes:**

#### **A. Implement Cursor Expiration**
Store cursors with a TTL (e.g., 1 hour).

**Example (Redis + Python):**
```python
r.setex(f"cursor:{cursor}", 3600, "valid")  # Expires in 1 hour
```

#### **B. Validate Cursors Before Use**
Check if a cursor still points to an existing record.

**Example (SQL):**
```sql
SELECT 1 FROM users WHERE id = :cursor LIMIT 1;
-- If 0 rows, cursor is invalid
```

#### **C. Use Optimistic Concurrency Control**
Compare expected vs. actual cursor values.

**Example (Python):**
```python
def validate_cursor(cursor, expected_value):
    if db.execute("SELECT id FROM users WHERE id = %s", (cursor,)) == []:
        raise ValueError("Cursor expired or invalid")
```

---

## **3. Debugging Tools and Techniques**

### **A. Logging and Monitoring**
- **Log cursor values** on each request to track usage.
- **Monitor DB query performance** (e.g., `EXPLAIN ANALYZE` in PostgreSQL).
- **Set up alerts** for slow pagination queries.

**Example (PostgreSQL `EXPLAIN`):**
```sql
EXPLAIN ANALYZE
SELECT * FROM users WHERE id > 100 ORDER BY id ASC LIMIT 20;
```

### **B. Database Inspection**
- Check for **missing indexes** (`pg_stat_user_indexes` in PostgreSQL).
- Verify **table statistics** (`ANALYZE` command).
- Look for **full table scans** in slow query logs.

**Example (MySQL Slow Query Log):**
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  # Log queries > 1s
```

### **C. Cursor Flow Testing**
Manually test cursor progression:
1. Fetch page 1 → Check `nextPageCursor`.
2. Fetch page 2 with the cursor → Verify no duplicates/missing data.
3. Simulate concurrent writes → Check for races.

**Example (Python Test):**
```python
def test_cursor_flow():
    cursor = None
    for _ in range(5):
        data = get_paginated_data(cursor)
        assert len(data) == 20
        cursor = data["nextPageCursor"]
        assert cursor is not None
```

### **D. Distributed Tracing**
Use tools like **OpenTelemetry** or **Datadog** to trace pagination requests across microservices.

**Example (OpenTelemetry):**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("pagination_request"):
    data = get_paginated_data(cursor)
```

---

## **4. Prevention Strategies**

### **A. Design for Scalability**
- **Use compound cursors** (e.g., `table_id + sort_column`) for large datasets.
- **Avoid `LIMIT-OFFSET`** (it’s slow and inefficient).
- **Cache hot cursors** (e.g., home feeds, trending posts).

### **B. Handle Edge Cases Early**
| Edge Case | Solution |
|-----------|----------|
| `NULL` cursor | Default to min/max value |
| Missing records | Return empty list + `isLastPage: true` |
| Concurrent deletes | Use soft deletes or optimistic locking |
| Large datasets | Implement server-side filtering |

### **C. Automated Testing**
- **Unit tests** for cursor generation.
- **Integration tests** for end-to-end pagination.
- **Load tests** to simulate high concurrency.

**Example (Pytest):**
```python
def test_pagination_cursor_increment():
    # Insert test data
    for i in range(100):
        db.execute("INSERT INTO users (id) VALUES (%s)", (i,))

    # Test cursor progression
    cursor = None
    for _ in range(5):
        data = db.execute("SELECT id FROM users WHERE id > %s LIMIT 20", (cursor,))
        assert len(data) == 20
        cursor = data[-1]["id"]  # Next cursor
```

### **D. Documentation and Clear API Contracts**
- Document **cursor format** (e.g., "Hex-encoded SHA-256").
- Explain **expiration behavior** (e.g., "Cursors expire after 1 hour").
- Provide **examples** for initial and next-page requests.

**Example API Response:**
```json
{
  "data": [/* records */],
  "nextPageCursor": "abc123...",  // Hex string
  "isLastPage": false
}
```

---

## **5. Summary Checklist for Quick Resolution**
| Task | Tool/Command | Fix Applied? |
|------|-------------|--------------|
| Check for missing `ORDER BY` | `EXPLAIN ANALYZE` | ⬜ |
| Validate cursor format | Log cursor values | ⬜ |
| Ensure proper indexing | `CREATE INDEX` | ⬜ |
| Test race conditions | Transaction isolation | ⬜ |
| Monitor slow queries | Slow query logs | ⬜ |
| Implement cursor expiration | Redis TTL | ⬜ |
| Test edge cases | Manual cursor flow | ⬜ |

---

## **Final Recommendations**
1. **Start with simple cursors** (e.g., auto-increment IDs) before complex formats.
2. **Monitor database performance** regularly (`EXPLAIN ANALYZE`).
3. **Test under load** to catch race conditions early.
4. **Document assumptions** (e.g., "Cursors expire after 1 hour").
5. **Use transactions** for cursor generation in high-concurrency systems.

By following this guide, you can systematically debug and optimize keyset pagination for performance and reliability.