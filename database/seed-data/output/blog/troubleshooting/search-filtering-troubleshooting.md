# **Debugging Search & Filtering Patterns: A Troubleshooting Guide**

## **1. Introduction**
Search and filtering are critical for applications handling large datasets. Poor performance, incorrect results, or slow responses degrade user experience. This guide provides a structured approach to debugging common issues in search and filtering implementations.

---

## **2. Symptom Checklist**
Before diving into fixes, identify symptoms to narrow down potential causes:

| **Symptom**                     | **Possible Root Cause**                          |
|----------------------------------|--------------------------------------------------|
| Search takes >2s to respond      | Missing indexing, full-text scan on large tables |
| No autocomplete suggestions      | No stemming/tokenization in search logic         |
| Exact-match-only filtering       | Incorrect query builder (e.g., `=` instead of `LIKE`) |
| Faceted search returns no data  | Missing aggregations or incorrect field indexing |
| Poor relevance ranking           | Missing scoring (TF-IDF, BM25) or no weights     |
| High memory usage                | Unoptimized caching or inefficient joins         |
| API timeouts on large datasets  | No pagination or inefficient query execution     |

---
## **3. Common Issues & Fixes**

### **3.1 Slow Queries**
**Symptom:** "SELECT * FROM products WHERE name LIKE '%term%'" takes 5+ seconds.

**Root Cause:**
- Full-text scan on large tables.
- No indexing on searchable fields.

**Fix (PostgreSQL Example):**
```sql
-- Enable GIN index for full-text search
CREATE INDEX idx_products_name_gin ON products USING gin(to_tsvector('english', name));
```
**Alternative (Elasticsearch):**
```json
PUT /products
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "english"
      }
    }
  }
}
```

**Debugging Steps:**
1. Check query execution plan (`EXPLAIN ANALYZE` in PostgreSQL).
2. If using Elasticsearch, run `_explain` API to analyze scoring.

---

### **3.2 No Autocomplete**
**Symptom:** Users type "app" but get no "apple" suggestions.

**Root Cause:**
- Missing tokenization (e.g., no stemming, no fuzzy matching).

**Fix (Python - Elasticsearch Example):**
```python
from elasticsearch import Elasticsearch

es = Elasticsearch()
query = {
    "query": {
        "match": {
            "name": {
                "query": "app",
                "fuzziness": "AUTO"  # Adds fuzzy matching
            }
        }
    }
}
```
**Debugging Steps:**
1. Verify analyzer configuration in Elasticsearch (`/products/_analyze`).
2. Test with `fuzziness: "AUTO"` to allow typos.

---

### **3.3 Exact-Match Filtering**
**Symptom:** `WHERE category = "electronics"` returns nothing.

**Root Cause:**
- String comparison instead of `LIKE` or pattern matching.

**Fix (SQL):**
```sql
-- Use ILIKE for case-insensitive matching
SELECT * FROM products WHERE ILIKE('%electronics%');
```
**Fix (Elasticsearch):**
```json
{
  "query": {
    "wildcard": {
      "category": "electronics*"
    }
  }
}
```

**Debugging Steps:**
1. Check database logs for exact query.
2. Verify field type (e.g., not `INT` when expecting `STRING`).

---

### **3.4 Poor Relevance Ranking**
**Symptom:** Results don’t match user intent.

**Root Cause:**
- No scoring logic (e.g., keyword density, field weights).

**Fix (Elasticsearch):**
```json
{
  "query": {
    "multi_match": {
      "query": "wireless headphones",
      "fields": [
        {"name": {"boost": 2}},  # Boost name field
        {"description": {"boost": 1}}
      ]
    }
  }
}
```
**Debugging Steps:**
1. Run `_search?explain=true` to inspect scoring.
2. Adjust `boost` values to prioritize fields.

---

### **3.5 No Faceted Search Results**
**Symptom:** "Filter by price" returns no data.

**Root Cause:**
- Missing aggregations in Elasticsearch/SQL.

**Fix (Elasticsearch):**
```json
{
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"to": 100},
          {"from": 100, "to": 500},
          {"gt": 500}
        ]
      }
    }
  }
}
```

**Debugging Steps:**
1. Check Elasticsearch aggregations API (`/products/_search?aggs=...`).
2. Verify data exists in filtered ranges.

---

## **4. Debugging Tools & Techniques**

### **4.1 SQL Debugging**
- **`EXPLAIN ANALYZE`** – Check query performance.
  ```sql
  EXPLAIN ANALYZE SELECT * FROM products WHERE name LIKE '%term%';
  ```
- **Database slow query logs** – Filter for long-running queries.

### **4.2 Elasticsearch Debugging**
- **`_explain` API** – Debug relevance scores.
  ```json
  POST /products/_search
  {
    "_explain": true,
    "query": { "match": { "name": "shoes" } }
  }
  ```
- **Dev Tools (`_analyze`)** – Test tokenization.
  ```json
  POST /products/_analyze
  { "analyzer": "standard", "text": "wireless headphones" }
  ```

### **4.3 Application-Level Debugging**
- **Log query parameters** – Ensure filters are applied correctly.
  ```python
  print(f"Searching for: {query_params}")  # Log before executing
  ```
- **Implement query timeouts** – Prevent hanging queries.
  ```python
  # Elasticsearch client config
  client = Elasticsearch(timeout=10)  # 10s timeout
  ```

---

## **5. Prevention Strategies**

### **5.1 Indexing & Schema Design**
- **Database:** Use full-text indexes (PostgreSQL `GIN`, MySQL `FULLTEXT`).
- **Elasticsearch:** Define analyzers and mappings properly.

### **5.2 Caching Strategies**
- **Redis/Memcached:** Cache frequent search queries.
  ```python
  @lru_cache(maxsize=1000)
  def search_products(query: str) -> list:
      # Logic here
  ```

### **5.3 Query Optimization**
- **Pagination:** Use `LIMIT/OFFSET` or keyset pagination.
  ```sql
  SELECT * FROM products
  WHERE id > last_seen_id
  ORDER BY id
  LIMIT 20;
  ```
- **Debounce Input:** Delay autocomplete requests until user pauses typing.

### **5.4 Monitoring & Alerts**
- **Prometheus + Grafana:** Track query latency.
- **Set alerts** for slow queries (e.g., >500ms).

---

## **6. Summary Checklist**
| **Issue**               | **Quick Fix**                          | **Debugging Step**                     |
|-------------------------|----------------------------------------|----------------------------------------|
| Slow queries            | Add index/optimize query               | `EXPLAIN ANALYZE`                      |
| No autocomplete         | Enable fuzzy matching                  | Test `_analyze` in Elasticsearch      |
| Exact-match filtering   | Use `LIKE`/`ILIKE`                     | Verify query logs                      |
| Poor relevance          | Adjust `boost` in scoring              | Run `_explain` API                     |
| No faceted results      | Check aggregations                     | Test `/_search?aggs`                   |

---
## **7. Final Notes**
- **Start with the slowest queries** (identify via monitoring).
- **Test locally** before deploying fixes.
- **Benchmark changes** to ensure performance improves.

By following this guide, you can systematically resolve search and filtering issues while ensuring scalable, user-friendly experiences.