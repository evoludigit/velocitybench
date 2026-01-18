# **[Pattern] Reference Guide: Soft Delete Performance Optimization**

---

## **Overview**
The **Soft Delete Performance** pattern addresses scalability challenges introduced by querying records marked as "deleted" (`deleted_at` is non-`NULL`) while maintaining high-performance reads. Unlike hard deletes, soft deletes preserve data integrity (e.g., for audit trails) but require efficient filtering.

### **Key Goals**
- **Minimize performance overhead** when querying active records (`deleted_at IS NULL`).
- **Optimize storage** by skipping unnecessary data deletion.
- **Balance consistency** between reads and writes.

---

## **Schema Reference**

| Field          | Type            | Description                                                                                     | Example Value                     |
|----------------|-----------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `deleted_at`   | `TIMESTAMP`     | Timestamp marking when record was soft-deleted (nullable).                                       | `2024-01-15 14:30:00` (or `NULL`) |
| **Index**      |                 | Performance-critical index on `deleted_at` for efficient filtering.                               | `CREATE INDEX idx_deleted_at ON records(deleted_at);` |

---

## **Implementation Details**

### **1. Filtering Active Records**
To exclude soft-deleted records, **always use `deleted_at IS NULL`** instead of `deleted_at = NULL` for compatibility with database engines (e.g., SQLite).

**Best Practice:**
```sql
-- ✅ Efficient: Uses an index-friendly condition
SELECT * FROM records WHERE deleted_at IS NULL;
```

### **2. Query Optimization**
#### **Avoid Full Table Scans**
- Ensure the `deleted_at` column is indexed.
- Use **composite indexes** if querying with other columns:
  ```sql
  CREATE INDEX idx_active_records ON records(id, deleted_at);
  ```
  This speeds up queries like:
  ```sql
  SELECT * FROM records WHERE id = 123 AND deleted_at IS NULL;
  ```

#### **Partitioning (Large Datasets)**
For tables with **millions of records**, partition by `deleted_at` ranges:
```sql
-- PostgreSQL example
CREATE TABLE records (
    id INT,
    deleted_at TIMESTAMP,
    -- other columns
)
PARTITION BY RANGE (deleted_at);
```

---

### **3. Update Strategies**
#### **Soft Delete Operation**
```sql
UPDATE records SET deleted_at = CURRENT_TIMESTAMP WHERE id = 123;
```
- **Optimization:** Batch updates (e.g., `WHERE user_id = 42`) to reduce lock contention.

#### **Hard Delete (Optional)**
To reclaim storage, periodically delete old soft-deletes:
```sql
DELETE FROM records WHERE deleted_at < CURRENT_DATE - INTERVAL '30 days';
```
- **Caution:** Ensure no active queries rely on these records.

---

### **4. Application Integration**
#### **ORM Considerations**
- **ActiveRecord (Rails):**
  ```ruby
  # Add scope for soft-deleted records
  scope :active, -> { where(deleted_at: nil) }
  ```
- **Entity Framework (C#):**
  ```csharp
  // Filter in LINQ
  context.Records.Where(r => r.DeletedAt == null);
  ```

#### **Caching Strategies**
- Cache active records with a TTL (e.g., Redis key: `active_records:user_42`).
- Invalidate cache on soft-deletes.

---

## **Query Examples**

### **Query 1: Fetch Active Records**
```sql
-- Standard query (indexed)
SELECT * FROM records WHERE deleted_at IS NULL;
```

### **Query 2: Count Active Records**
```sql
-- Fast count (indexed)
SELECT COUNT(*) FROM records WHERE deleted_at IS NULL;
```

### **Query 3: Paginated Active Records**
```sql
-- Limit + Offset (index-friendly)
SELECT * FROM records WHERE deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 10 OFFSET 100;
```

### **Query 4: Partial Deletion (Retention Logic)**
```sql
-- Only delete records older than X days
DELETE FROM records
WHERE deleted_at < (CURRENT_TIMESTAMP - INTERVAL '7 days');
```

---

## **Performance Pitfalls & Mitigations**

| Pitfall                          | Impact                          | Solution                                  |
|-----------------------------------|---------------------------------|-------------------------------------------|
| Missing `deleted_at` index       | Full table scan                 | Add `CREATE INDEX idx_deleted_at`.        |
| `deleted_at = NULL` instead of `IS NULL` | Syntax errors in some DBs | Always use `IS NULL`.                     |
| Unbounded soft-deletes           | Storage bloat                    | Implement retention policies (e.g., >30d).|
| No composite indexes             | Slow joins                      | Add `idx_records_user_id_deleted_at`.     |

---

## **Related Patterns**

1. **[Event Sourcing for Audit Trails](link)**
   Log soft-deletes as domain events for replayability.

2. **[CQRS with Read/Write Separation](link)**
   Use different schemas for active/inactive data (e.g., `records_active`).

3. **[Optimistic Locking](link)**
   Combine with soft deletes to avoid write conflicts.

4. **[Database Sharding](link)**
   Partition soft-deleted records across shards for scalability.

---

## **Tools & Extensions**
- **Database-Level:**
  - **PostgreSQL:** `pg_partman` for automated partitioning.
  - **MySQL:** `PARTITION BY RANGE` for partitioned tables.
- **ORM Extensions:**
  - **Django:** `django-soft-deletes` library.
  - **Laravel:** `spatie/laravel-soft-deletes`.

---
**Note:** Always benchmark queries with realistic datasets and adjust indexing based on usage patterns.