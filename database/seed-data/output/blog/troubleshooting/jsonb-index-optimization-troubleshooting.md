# **Debugging [Pattern]: JSONB Index Optimization – A Troubleshooting Guide**
*Focused on Gin/Gist Indexes in PostgreSQL*

---

## **1. Introduction**
JSONB indexes in PostgreSQL (using **GIN** and **GiST** operators) are powerful for querying nested or semi-structured data. However, they can introduce performance bottlenecks if misconfigured.

This guide covers common issues, debugging techniques, and optimization strategies to resolve JSONB indexing problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm these symptoms:

✅ **Slow Queries** – JSONB queries (e.g., `->>`, `@>`, `?`) are significantly slower than expected.
✅ **High CPU Usage** – `pg_stat_statements` shows excessive CPU on `jsonb_ops` or `jsonb_index_ops`.
✅ **Index Not Used** – `EXPLAIN ANALYZE` reveals `Seq Scan` instead of `GinScan`/`GiSTScan`.
✅ **Large Index Size** – `pg_size_pretty(pg_total_relation_size('table'))` shows unusually large index growth.
✅ **Error: "Operator does not exist"** – Attempting to use unregistered operators (e.g., custom JSONB functions).

---

## **3. Common Issues & Fixes**

### **Issue 1: GIN Index Not Used (Full Table Scan)**
**Symptoms:** Queries ignore the index, forcing sequential scans.

**Root Causes:**
- Missing **operator classes** (e.g., `gin_trgm_ops` for text search).
- Incorrect **index definition** (wrong `jsonb_path_ops`).
- **Partial index conditions** (e.g., `WHERE jsonb_data @> '{"key": "value"}'` with missing parent clauses).

**Fixes:**
#### **A. Verify Index Usage**
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE data @> '{"name": "Alice"}';
```
- If it shows `Seq Scan`, the index is unused.

#### **B. Ensure Correct Operator Class**
```sql
-- Check if the operator class is registered
SELECT proname FROM pg_operator WHERE opfamily = 'gin_trgm_ops';
-- If missing, install it:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

#### **C. Rebuild the Index**
```sql
-- Drop and recreate the index (if misconfigured)
DROP INDEX IF EXISTS idx_users_data;
CREATE INDEX idx_users_data ON users USING gin (data gin_trgm_ops);
```

#### **D. Add Partial Index (If Applicable)**
If filtering on a parent key:
```sql
CREATE INDEX idx_users_data_active ON users (is_active) INCLUDE (data)
WHERE is_active = true;
```

---

### **Issue 2: High CPU on `jsonb_ops`**
**Symptoms:** `pg_stat_statements` shows high CPU for `jsonb_ops` or `jsonb_path_ops`.

**Root Causes:**
- **Overly broad queries** (e.g., `jsonb_data @> '{"*": "*"}'` scans all JSON fields).
- **Missing index on nested paths** (e.g., querying `data->>'name'` without an index).

**Fixes:**
#### **A. Optimize Queries**
```sql
-- Avoid wildcard searches
SELECT * FROM products WHERE attributes @> '{"color": "red"};'  -- Good
-- Instead of:
SELECT * FROM products WHERE attributes @> '{"*": "*"}';         -- Bad (scans all fields)
```

#### **B. Add Index on Specific Paths**
```sql
-- Index a specific JSONB path
CREATE INDEX idx_products_color ON products USING gin ((attributes->>'color'));
```

#### **C. Use `jsonb_path_ops` for String Matching**
```sql
-- Better than `text_pattern_ops`
CREATE INDEX idx_users_name_trgm ON users USING gin ((data->>'name') trgm_ops);
```

---

### **Issue 3: GiST Index Corruption**
**Symptoms:** Crashes on `GiST` operations, or slow performance in spatial JSONB queries.

**Root Causes:**
- Manual `VACUUM FULL` without `REINDEX`.
- Corrupted `GiST` structure (e.g., after a crash).

**Fixes:**
#### **A. Reindex the Table**
```sql
REINDEX TABLE users;
```

#### **B. Check for Corruption**
```sql
-- Force a vacuum to defragment GiST
VACUUM (VERBOSE, ANALYZE, REINDEX) users;
```

#### **C. Verify GiST Index Integrity**
```sql
-- Check if GiST is properly initialized
SELECT indexdef FROM pg_indexes WHERE tablename = 'users' AND indexdef LIKE '%USING GiST%';
```

---

### **Issue 4: Large Index Bloat**
**Symptoms:** `pg_size_pretty(pg_relation_size('idx_users_data'))` shows excessive growth.

**Root Causes:**
- **Improper index selection** (e.g., indexing entire JSONB column).
- **Frequent updates/deletes** without `VACUUM`.

**Fixes:**
#### **A. Optimize Index Size**
```sql
-- Instead of indexing full JSONB, index only needed fields
CREATE INDEX idx_users_name_email ON users (data->>'name', data->>'email');
```

#### **B. Automate Maintenance**
```sql
-- Enable auto-vacuum for high-traffic tables
ALTER TABLE users SET (autovacuum_vacuum_scale_factor = 0.1);
```

#### **C. Use Partial Indexes for Active Records**
```sql
CREATE INDEX idx_users_active_data ON users (data)
WHERE active_status = true;
```

---

### **Issue 5: Custom JSONB Operator Not Recognized**
**Symptoms:** Error: `ERROR: operator does not exist: jsonb @> jsonb`.

**Root Causes:**
- Missing **operator family** registration.
- Wrong **operator class** in the index.

**Fixes:**
#### **A. Register Custom Operator**
```sql
-- Example: Extend GIN for custom JSON comparisons
CREATE OPERATOR FUNCTION (jsonb_ops, @>)
WITH FUNCTION jsonb_gist_ops(@> jsonb, jsonb);
```

#### **B. Verify Index Compatibility**
```sql
-- Ensure the operator is supported
SELECT opfamily FROM pg_opfamily WHERE opname = '@>';
```

---

## **4. Debugging Tools & Techniques**

### **A. `EXPLAIN ANALYZE` Deep Dive**
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM users WHERE data @> '{"status": "active"}';
```
- Look for **cost estimates** (high `seq_page_cost` suggests index inefficiency).
- Check **buffer cache hits** (low hits indicate disk I/O bottlenecks).

### **B. `pg_stat_activity` for Blocking Queries**
```sql
SELECT pid, usename, query FROM pg_stat_activity WHERE query LIKE '%jsonb%';
```
- Identify long-running JSONB queries causing contention.

### **C. `pg_stat_user_indexes` for Index Usage**
```sql
SELECT schemaname, relname, indexrelname,
       idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname = 'users';
```
- **`idx_scan`** = Number of index scans.
- **`idx_tup_fetch`** = Tuples fetched from index (high ratio = inefficiency).

### **D. `pg_total_relation_size` for Index Bloat**
```sql
SELECT relname,
       pg_size_pretty(pg_relation_size(C.oid)) AS table_size,
       pg_size_pretty(pg_indexes_size(C.oid)) AS index_size
FROM pg_class C WHERE relname = 'users';
```

### **E. `pg_repack` for Large Index Reorganization**
```sql
-- Non-blocking index reorganization (if standard VACUUM fails)
pg_repack -d your_database -t users;
```

---

## **5. Prevention Strategies**

### **A. Index Design Best Practices**
✔ **Index only necessary paths** (avoid full-column GIN indexes).
✔ **Use partial indexes** for filtered subsets (e.g., `WHERE active = true`).
✔ **Combine GIN with BRIN** for large tables with temporal patterns.

### **B. Query Optimization**
✔ **Avoid `@> '{"*": "*"}'`** – Use specific fields instead.
✔ **Use `#>>` for nested lookups** (e.g., `data #>> '{nested,key}'`).
✔ **Leverage `jsonb_path_ops`** for text search (e.g., `LIKE` on JSONB).

### **C. Maintenance Automation**
```sql
-- Schedule regular maintenance
CREATE OR REPLACE FUNCTION vacuum_jsonb_indexes()
RETURNS void AS $$
BEGIN
    PERFORM vacuum(verbose => true, analyze => true, index_cleanup => true) ON users;
END;
$$ LANGUAGE plpgsql;

-- Run weekly
CREATE EVENT TRIGGER weekly_vacuum ON schedule
EVERY '1 week' DO EXECUTE FUNCTION vacuum_jsonb_indexes();
```

### **D. Monitoring Key Metrics**
- **Track `jsonb_ops` in `pg_stat_statements`**.
- **Set up alerts for `idx_scan` spikes**.
- **Monitor `pg_size_pretty(pg_total_relation_size())` trends**.

---

## **6. Final Checklist for Resolution**
| **Step** | **Action** | **Tool/Command** |
|----------|------------|------------------|
| **1** | Check if index is used | `EXPLAIN ANALYZE` |
| **2** | Verify operator class | `SELECT * FROM pg_opclass` |
| **3** | Rebuild index if misconfigured | `DROP INDEX; CREATE INDEX` |
| **4** | Optimize query logic | Replace `@> '{"*": "*"}'` |
| **5** | Monitor CPU/IO | `pg_stat_statements`, `pg_stat_activity` |
| **6** | Defragment GiST/GIN | `VACUUM (REINDEX)` |
| **7** | Automate maintenance | `pg_repack`, `AUTOVACUUM` |

---

## **7. Conclusion**
JSONB indexing with **GIN/GiST** is powerful but requires careful tuning. Focus on:
- **Correct index definitions** (check `opclass`).
- **Query optimization** (avoid wildcard `@>`).
- **Regular maintenance** (`VACUUM`, `REINDEX`).
- **Monitoring** (`pg_stat_user_indexes`, `EXPLAIN`).

By following this guide, you can diagnose and resolve JSONB performance issues efficiently. For persistent problems, consider **PostgreSQL 16+ features** (e.g., **JSONB partial indexes** and **better GiST optimizations**).