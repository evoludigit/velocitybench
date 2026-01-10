# **Debugging Full-Text Search in PostgreSQL: A Troubleshooting Guide**

## **1. Introduction**
PostgreSQL’s **Full-Text Search (FTS)** is a powerful feature for efficiently searching unstructured text. However, common issues like slow queries, poor relevance, or incorrect matches can degrade performance and user experience.

This guide provides a structured approach to diagnosing and resolving FTS-related problems.

---

## **2. Symptom Checklist**
Before diving into fixes, verify which symptoms apply:

| **Symptom** | **Possible Causes** |
|-------------|---------------------|
| ⚠ **Slow searches** | Missing GIN indexes, large search corpus, inefficient queries |
| ⚠ **Poor relevance** | Unoptimized `ts_vector` configuration, missing weights, incorrect ranking |
| ⚠ **Exact match only** | Missing stemming, case sensitivity, or synonym handling |
| ⚠ **No results** | Incorrect search term, missing `ts_config`, or wrong `ts_query` syntax |
| ⚠ **High CPU/memory usage** | Full-text scanning instead of using indexes |

---

## **3. Common Issues & Fixes**

### **Issue 1: Slow Searches (High Execution Time)**
**Symptoms:**
- `EXPLAIN ANALYZE` shows **sequential scans** (`Seq Scan`) instead of **GIN index scans** (`Gin Scan`).
- Queries take **seconds** even on small datasets.

#### **Debugging Steps:**
1. **Check if a GIN index exists:**
   ```sql
   SELECT indexname FROM pg_indexes WHERE tablename = 'your_table' AND indexdef LIKE '%gin%';
   ```
   - If missing, create it:
     ```sql
     CREATE INDEX idx_fts_search ON your_table USING GIN(to_tsvector('english', text_column));
     ```

2. **Verify query execution plan:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM your_table
   WHERE to_tsvector('english', text_column) @@ to_tsquery('english', 'search term');
   ```
   - **Expected:** Should use the GIN index.
   - **Fix:** If not, ensure the `to_tsvector()` function matches the index.

3. **Optimize `ts_vector` generation:**
   - If searching **dynamically**, consider materialized views:
     ```sql
     CREATE MATERIALIZED VIEW mv_fts AS
     SELECT id, to_tsvector('english', text_column) AS search_vec FROM your_table;
     CREATE INDEX idx_mv_fts ON mv_fts USING GIN(search_vec);
     ```

---

### **Issue 2: Poor Relevance (Wrong Search Results)**
**Symptoms:**
- The best matches appear **far from the top**.
- **Boolean queries (`&`, `|`, `!`)** don’t work as expected.

#### **Debugging Steps:**
1. **Check `ts_config` settings:**
   - Default: `'english'` (stemming, weighting).
   - If using a custom config:
     ```sql
     CREATE TEXT SEARCH CONFIGURATION custom_config (
       COPY = english
     );
     ALTER TEXT SEARCH CONFIGURATION custom_config
     ALTER MAPPING FOR asciiwords, hword_asciiword, word AS simple;
     ```
   - Rebuild `ts_vector` with the correct config:
     ```sql
     CREATE INDEX idx_fts ON your_table USING GIN(to_tsvector('custom_config', text_column));
     ```

2. **Use `ranking` for better relevance:**
   ```sql
   SELECT id, ts_rank_cd(search_vec, to_tsquery('english', 'search term')) AS rank
   FROM mv_fts
   WHERE search_vec @@ to_tsquery('english', 'search term')
   ORDER BY rank DESC;
   ```

3. **Adjust `ts_weight` for better matching:**
   - Example (prioritize longer words):
     ```sql
     SELECT to_tsvector('custom_config', 'this is a sample sentence')
     -- Adjust weights via config or use ts_headline() for highlights.
     ```

---

### **Issue 3: Exact Match Only (No Stemming/Lemmatization)**
**Symptoms:**
- `'running'` doesn’t match `'run'`, `'jumps'` doesn’t match `'jump'`.

#### **Debugging Steps:**
1. **Verify `english` config is used:**
   - The default `'english'` config performs stemming.
   - If using a custom config, ensure it includes:
     ```sql
     ALTER TEXT SEARCH CONFIGURATION custom_config
     ALTER MAPPING FOR word, hword, hword_asciiword AS stem;
     ```

2. **Manually test stemming:**
   ```sql
   SELECT to_tsvector('english', 'running') @@ to_tsquery('english', 'run');
   -- Should return 't' (true)
   ```

3. **Use `ts_headline()` for debugging:**
   ```sql
   SELECT ts_headline('english', search_vec, to_tsquery('english', 'term'));
   -- Helps see how PostgreSQL interprets searches.
   ```

---

### **Issue 4: No Results Despite Expected Matches**
**Symptoms:**
- Search terms exist but return **zero rows**.

#### **Debugging Steps:**
1. **Check if terms are indexed:**
   ```sql
   SELECT * FROM your_table WHERE to_tsvector('english', text_column) @@ to_tsquery('english', 'term');
   -- If empty, verify:
   SELECT to_tsvector('english', text_column) FROM your_table WHERE text_column LIKE '%term%';
   ```

2. **Test with a raw `ts_query`:**
   ```sql
   SELECT * FROM your_table WHERE to_tsvector('english', text_column) @@ 'term:';
   -- If still empty, check for:
   - Missing whitespace (e.g., `'apple'` vs `'apple '`)
   - Stop words (e.g., `'and'`, `'the'` are excluded by default)
   ```

3. **Exclude stop words (if needed):**
   ```sql
   SELECT to_tsvector('english', 'the quick brown fox') @@ 'fox';
   -- Will return false because 'the' is a stopword.
   -- Use 'no' to include:
   SELECT to_tsvector('english', 'the quick brown fox') @@ 'fox:no';
   ```

---

## **4. Debugging Tools & Techniques**

### **A. `EXPLAIN ANALYZE`**
- Identifies if the GIN index is being used.
- Example:
  ```sql
  EXPLAIN ANALYZE
  SELECT * FROM articles
  WHERE to_tsvector('english', content) @@ 'postgresql:no';
  ```

### **B. `pg_stat_statements`**
- Measures slow FTS queries:
  ```sql
  CREATE EXTENSION pg_stat_statements;
  -- Check slow queries:
  SELECT query, calls, total_time FROM pg_stat_statements
  WHERE query LIKE '%to_tsquery%'
  ORDER BY total_time DESC;
  ```

### **C. `ts_debug` and `ts_vector` Inspection**
- Check how terms are tokenized:
  ```sql
  SELECT ts_debug('english', 'running');
  -- Output: {'running', 'run'}
  ```

### **D. `ts_headline()` for Highlighting**
- Helps verify if the right terms are matched:
  ```sql
  SELECT ts_headline('english', to_tsvector('english', content), to_tsquery('english', 'debug'))
  FROM articles;
  ```

---

## **5. Prevention Strategies**

### **A. Indexing Best Practices**
- **Always use GIN indexes** for `ts_vector`:
  ```sql
  CREATE INDEX ON your_table USING GIN(to_tsvector('english', text_column));
  ```
- **Update indexes when data changes** (e.g., with `TRIGGER` or `PARTIAL` updates).

### **B. Optimizing `ts_config`**
- Use a **custom config** for special cases:
  ```sql
  CREATE TEXT SEARCH CONFIGURATION my_config (
    COPY = english
  );
  ALTER TEXT SEARCH CONFIGURATION my_config
  ALTER MAPPING FOR word AS stem;
  ```
- **Test different configurations** before production deployment.

### **C. Avoid Full-Text Scanning**
- **Never search directly on text** without `ts_vector`:
  ```sql
  -- ❌ Bad (slow)
  WHERE content LIKE '%term%';

  -- ✅ Good (fast)
  WHERE to_tsvector('english', content) @@ to_tsquery('english', 'term');
  ```

### **D. Monitor with `pg_stat_user_tables`**
- Check FTS usage:
  ```sql
  SELECT relname, n_live_tup FROM pg_stat_user_tables
  WHERE relname LIKE '%your_table%';
  ```

### **E. Use `ts_stat()` for Token Counts**
- Debug stemming behavior:
  ```sql
  SELECT ts_stat('english', 'running');
  -- Example output: {'run': 1}
  ```

---

## **6. Summary of Key Fixes**
| **Issue** | **Quick Fix** |
|-----------|--------------|
| **Slow queries** | Add GIN index, use `EXPLAIN ANALYZE` |
| **Poor relevance** | Use `ts_rank_cd()`, adjust `ts_config` |
| **Exact match only** | Ensure `english` config is used |
| **No results** | Check stop words, whitespace, and `to_tsquery` syntax |
| **High CPU** | Ensure `ts_vector` is indexed |

## **7. Final Checklist**
1. ✅ **Verify GIN indexes exist** on `ts_vector` columns.
2. ✅ **Check `EXPLAIN ANALYZE`** for index usage.
3. ✅ **Test `ts_debug()`** for stemming behavior.
4. ✅ **Use `ts_rank_cd()`** for better relevance.
5. ✅ **Monitor slow queries** with `pg_stat_statements`.

By following this guide, you should resolve most FTS issues efficiently. If problems persist, consider **upgrading PostgreSQL** (newer versions optimize FTS better) or **rewriting queries** to use **materialized views** for large datasets.