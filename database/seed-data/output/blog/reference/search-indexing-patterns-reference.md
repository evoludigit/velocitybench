# **[Pattern] Full-Text Search with Elasticsearch Reference Guide**

---

## **1. Overview**
This reference guide details the **Full-Text Search & Indexing Pattern** using **Elasticsearch**, a distributed search and analytics engine. It covers core concepts, implementation best practices, schema design, query techniques, and scaling strategies for high-performance search solutions.

The pattern describes how to efficiently **index structured/unstructured data** (e.g., logs, documents, product catalogs) for **fast, relevant full-text searches**, including **fuzzy matching, faceted navigation, and geospatial queries**. It aligns with **Elasticsearch’s inverted index** architecture while addressing scalability, performance tuning, and maintainability.

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 | **Example Use Case**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Index**              | A collection of documents (similar to a database table) with a schema-defined mapping (field types, analyzers).                                                                                             | `products`, `orders`, `customer_reviews` indices.                                                      |
| **Document**           | A JSON object mapped to an index (e.g., a product record).                                                                                                                                                     | `{"id": "123", "name": "Laptop", "price": 999, "description": "16GB RAM..."}`                         |
| **Shard**              | A subset of an index, distributed across nodes for horizontal scaling.                                                                                                                                      | Splitting `products` into `products-shard-1` and `products-shard-2` for faster searches.               |
| **Inverted Index**     | Underlying data structure mapping terms to document IDs for fast full-text lookup.                                                                                                                         | `"apple"` → `[doc1, doc3, doc7]` (documents containing the term).                                      |
| **Analyzer**           | Tokenizes text (e.g., splits sentences into keywords, applies stemming). Standard vs. custom analyzers (e.g., `english`, `icu_analyzer`).                                                              | Analyzing `"running"` → `["run"]` (stemming) or `["run", "run-n"]` (nginx).                              |
| **Token Filter**       | Post-processing for tokens (e.g., lowercase, synonyms).                                                                                                                                                      | Replacing `"MacBook"` with `["macbook", "mac book"]`.                                                  |
| **Tokenizer**          | Splits text into tokens (e.g., `keyword`, `whitespace`, `icu_tokenizer`).                                                                                                                                   | Splitting `"Elasticsearch"` → `["Elasticsearch"]` (keyword) vs. `["elastic", "search"]` (standard).   |
| **Mapping**            | Defines field types (e.g., `text`, `keyword`, `integer`) and analyzers.                                                                                                                                       | `{ "price": { "type": "float" }, "tags": { "type": "keyword" } }`                                      |
| **Facet/Bucket**       | Aggregates document counts by field (e.g., `price_range`, `category`).                                                                                                                                         | Counting products in `["Electronics", "Books"]` categories.                                           |
| **Refresh Interval**   | How often documents are made searchable (default: `1s`). Lower values improve query accuracy but reduce write throughput.                                                                                   | Setting `refresh_interval: "30s"` for bulk indexing.                                                    |
| **Replicas**           | Copies of primary shards for fault tolerance.                                                                                                                                                                | 1 replica per shard in `products` index for high availability.                                        |
| **Search API**         | REST endpoints (`GET /_search`) for queries (DSL, Painless scripting).                                                                                                                                           | `GET /products/_search?q=laptop&size=10`.                                                                 |

---

## **3. Schema Design**

### **3.1 Core Field Types**
| **Field Type** | **Use Case**                                                                 | **Indexing**                          | **Searchability**                     |
|----------------|------------------------------------------------------------------------------|---------------------------------------|----------------------------------------|
| `text`         | Full-text search (analyzed).                                                 | Tokenized, stored as inverted index. | `match`, `multi_match`, `query_string`. |
| `keyword`      | Exact matches (e.g., IDs, tags).                                            | No analysis; stored as-is.           | `term`, `terms`, `filter` clauses.     |
| `integer`/`float` | Numeric filters/aggregations.                                              | Stored as-is.                         | `range`, `stats`, `avg` aggregations.  |
| `date`         | Time-based filtering.                                                        | Stored in epoch milliseconds.         | `range`, `date_histogram`.             |
| `ip`           | IP address comparisons.                                                      | Stored as numeric.                    | `range`, `geo_bounds`.                |
| `geo_point`    | Location data (latitude/longitude).                                          | Stored as GeoJSON.                    | `geo_distance`, `geo_bounds`.          |

---

### **3.2 Example Schema: E-Commerce Product Index**
```json
PUT /products
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "tokenizer": "autocomplete_tokenizer",
          "filter": ["lowercase", "asciifolding"]
        }
      },
      "tokenizer": {
        "autocomplete_tokenizer": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 10
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text", "analyzer": "autocomplete" },
      "description": { "type": "text" },
      "price": { "type": "float" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "rating": { "type": "float" },
      "stock": { "type": "integer" },
      "created_at": { "type": "date" },
      "specs": {
        "type": "object",
        "properties": {
          "ram": { "type": "keyword" },
          "storage": { "type": "keyword" }
        }
      }
    }
  }
}
```
**Key Notes:**
- `edge_ngram` tokenizer enables autocomplete (e.g., `"lapt"` → `["lap", "apt", ...]`).
- `specs` uses nested objects for complex hierarchies (query via `nested` clause).
- `description` uses default `standard` analyzer for full-text search.

---

## **4. Query Examples**

### **4.1 Basic Search (Full-Text)**
```json
GET /products/_search
{
  "query": {
    "match": {
      "description": "bluetooth speakers with deep bass"
    }
  }
}
```
- **Behavior**: Scores documents by TF-IDF relevance (e.g., `"deep bass"` appears often in few docs).

---

### **4.2 Fuzzy Matching (Typos)**
```json
GET /products/_search
{
  "query": {
    "fuzzy": {
      "name": {
        "value": "Macbook",
        "fuzziness": "AUTO"  // Default: 2 characters
      }
    }
  }
}
```
- **Use Case**: Find `MacBook` when user searches `Macbook` or `Macbookk`.

---

### **4.3 Multi-Field Search**
```json
GET /products/_search
{
  "query": {
    "multi_match": {
      "query": "wireless headphones",
      "fields": ["name^3", "description"]
    }
  }
}
```
- **Behavior**: Boosts `name` field (`^3`) by 3x in scoring.

---

### **4.4 Faceted Navigation (Aggregations)**
```json
GET /products/_search
{
  "aggs": {
    "categories": { "terms": { "field": "category" } },
    "price_ranges": {
      "range": { "field": "price", "ranges": [{ "to": 50 }, { "from": 50, "to": 200 }, ...] }
    }
  }
}
```
- **Output**: `{ "categories": {"buckets": [{"key": "Electronics", "doc_count": 100}, ...]} }`

---

### **4.5 Geospatial Search (Nearby Stores)**
```json
GET /stores/_search
{
  "query": {
    "geo_distance": {
      "distance": "5km",
      "location": { "lat": 37.7749, "lon": -122.4194 }  // San Francisco
    }
  },
  "_source": ["name", "address"]
}
```
- **Use Case**: Find stores within 5km of a user’s location.

---

### **4.6 Compound Queries (Boolean Logic)**
```json
GET /products/_search
{
  "query": {
    "bool": {
      "must": [{ "match": { "category": "headphones" } }],
      "filter": [
        { "range": { "price": { "lte": 100 } } },
        { "term": { "stock": { "value": true } } }
      ]
    }
  }
}
```
- **Behavior**: Only documents where:
  - `category = headphones` (required),
  - `price <= 100` (filter, no scoring impact),
  - `stock = true`.

---

### **4.7 Scripted Fields (Dynamic Calculations)**
```json
GET /products/_search
{
  "aggs": {
    "profit_margin": {
      "scripted_metric": {
        "init_script": "state.margin = 0; state.count = 0;",
        "map_script": "if (doc['cost'].value > 0) { state.margin += doc['price'].value - doc['cost'].value; state.count++; }",
        "combine_script": "state.margin += params.map_state.margin; state.count += params.map_state.count;",
        "reduce_script": "return state.margin / state.count;"
      }
    }
  }
}
```
- **Use Case**: Compute average profit margin across all products.

---

## **5. Performance Best Practices**

| **Best Practice**               | **Action Items**                                                                                                                                                                                                 | **Impact**                                                                                  |
|----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Sharding Strategy**            | Distribute shards across nodes (1 shard/10GB data; adjust `number_of_shards` for write throughput).                                                                                                           | Avoids hotspots; balances load.                                                               |
| **Refresh Rate**                 | Increase `refresh_interval` (e.g., `30s`) for bulk indexing; lower for near-real-time searches.                                                                                                               | Trade-off: Lower refresh → faster writes but stale searches.                               |
| **Fielddata Caching**            | Use `doc_values` for `keyword` fields (e.g., `category`) instead of `fielddata` for sorting/aggregations.                                                                                                       | Reduces memory pressure; speeds up `sort` and `terms` aggregations.                        |
| **Analyzer Selection**           | Prefer `keyword` for exact matches; use `text` + custom analyzers for full-text. Avoid excessive tokenizers (e.g., `icu_tokenizer` is slow).                                                                         | Optimizes indexing/search time.                                                               |
| **Pagination**                   | Use `search_after` (deep pagination) instead of `from/size` for large result sets.                                                                                                                                | Avoids scroll API overhead; supports primary-key-based pagination.                        |
| **Replicas**                     | Set `number_of_replicas: 1` for production; higher values improve read availability but consume storage.                                                                                                       | Balance availability vs. disk usage.                                                        |
| **Bulk API**                     | Use `POST /_bulk` with multi-threaded clients (e.g., Logstash). Batch size: 1–5MB.                                                                                                                                   | Maximizes throughput (100K+ docs/sec).                                                       |
| **Synonyms Filters**             | Add synonyms to analyzers for search normalization (e.g., `"USA" => "United States"`).                                                                                                                                | Improves relevance for variant queries.                                                     |
| **ILM (Index Lifecycle Management)** | Automate index rollover, retention, and snapshots (e.g., `hot-warm-cold-archive` tiers).                                                                                                                          | Reduces maintenance overhead; enables long-term data retention.                              |

---

## **6. Related Patterns**

| **Pattern**                          | **Description**                                                                                                                                                                                                 | **Elasticsearch Integration**                                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Time-Series Data Pattern**         | Ingest and analyze metrics/logs (e.g., IoT sensors) with time-based aggregations.                                                                                                                                 | Use `time_series` index templates; query with `date_histogram`, `stats` aggregations.                          |
| **Log Analysis Pattern**             | Centralize logs (e.g., Apache, Kubernetes) for structured search/filtering.                                                                                                                                  | Use `ingest pipelines` for log parsing; search with `keyword`/`text` fields.                                   |
| **Autocomplete Pattern**             | Implement prefix/search-as-you-type suggestions.                                                                                                                                                            | Combine `edge_ngram` tokenizer with `completion` field type.                                             |
| **Geospatial Search Pattern**        | Location-based queries (e.g., "restaurants near me").                                                                                                                                                           | Use `geo_point` + `geo_distance`/`geo_bounds` queries.                                                   |
| **Machine Learning (ML) Pattern**    | Anomaly detection or recommendation engines (e.g., "Customers who bought X also bought Y").                                                                                                                       | Train ML models via `GET /_ml/start`; deploy via `ml` index.                                             |
| **Hybrid Search Pattern**            | Combine full-text + vector embeddings (e.g., semantic search).                                                                                                                                                | Use `dense_vector` field type with `kknn` plugin for similarity search.                                      |
| **Audit Log Pattern**                | Track user actions (e.g., `GET /products/123`) for compliance.                                                                                                                                                | Index logs as `timestamp, user_id, action, resource`; analyze with `date_range` filters.                     |

---

## **7. Troubleshooting**

| **Issue**                          | **Diagnosis**                                                                                                                                                                                                 | **Solution**                                                                                                   |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Slow Searches**                   | High cardinality on `keyword` fields (e.g., `user_id`) or missing `doc_values`.                                                                                                                      | Use `keyword` for filters only; enable `doc_values` for sorting/aggregations.                              |
| **High CPU Usage**                  | Overuse of `fielddata` (e.g., sorting by `text` field).                                                                                                                                                 | Avoid `sort` on `text` fields; use `doc_values` or `keyword` aliases.                                       |
| **Bulk API Errors**                 | Malformed JSON or exceeding batch size (15MB limit).                                                                                                                                                       | Split batches; validate JSON with `POST /_bulk?pretty=true`.                                                |
| **Shard Allocation Failures**       | Disk pressure or node failures.                                                                                                                                                                       | Check cluster health (`GET /_cluster/health`), expand disk capacity, or adjust `shard.allocation.awareness`. |
| **Stale Aggregations**              | Refresh lag during bulk loads.                                                                                                                                                                         | Increase `refresh_interval` or use `wait_for_active_shards: all` in bulk requests.                      |
| **Memory Pressure**                 | Too many open segments (high `mergedSegments`).                                                                                                                                                            | Run `forcemerge` API or optimize analyzer complexity.                                                      |

---

## **8. References**
- [Elasticsearch Official Docs](https://www.elastic.co/guide/)
- [Index Lifecycle Management (ILM)](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html)
- [Analyzers & Tokenizers](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html)
- [Bulk API Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html)