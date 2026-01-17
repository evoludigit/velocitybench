# **[Pattern] Search & Filtering Reference Guide**

---

## **1. Overview**
The **Search & Filtering** pattern enables fast, scalable discovery of data across large datasets by combining:
- **Full-text search** (for keyword matching)
- **Structured filtering** (for predicates like category, price range, or date)
- **Aggregations & faceting** (for statistical breakdowns and interactive exploration)

Traditional relational database queries struggle with datasets >100K records. Instead, this pattern leverages:
- **Elasticsearch** (full-text indexing + inverted index)
- **GraphQL filters** (for REST APIs)
- **Client-side UI components** (e.g., dropdowns, sliders)

Use cases include:
- E-commerce product catalogs
- Document repositories
- Log analysis dashboards
- Knowledge bases

---

## **2. Schema Reference**

| **Component**       | **Description**                                                                 | **Data Type**               | **Notes**                                  |
|---------------------|-------------------------------------------------------------------------------|-----------------------------|--------------------------------------------|
| **Full-Text Index** | Stores raw text (e.g., product descriptions) for keyword search.             | `text` (analyzed)           | Elasticsearch `text` field enables fuzzy matching. |
| **Structured Fields** | Key filterable attributes (e.g., `price`, `category`, `published_date`).     | `keyword`, `integer`, `date` | Use `keyword` for exact matches (e.g., tags). |
| **Facets**          | Pre-aggregated stats (e.g., count of products per category).                 | `nested` or `bucket aggregates` | Reduces client/server round trips.        |
| **Pagination**      | Limits results per page (e.g., `limit=20`, `offset=0`).                      | `integer`                   | Critical for performance.                 |

---

## **3. Key Implementation Concepts**

### **3.1 Full-Text Search**
- **Elasticsearch Setup**:
  ```json
  PUT /products
  {
    "settings": {
      "analysis": {
        "filter": {
          "autocomplete_filter": { "type": "edge_ngram", "min_gram": "2", "max_gram": "10" }
        },
        "analyzer": {
          "autocomplete": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "autocomplete_filter"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "description": { "type": "text", "analyzer": "autocomplete" }
      }
    }
  }
  ```

- **Query Example** (search for "wireless headphones"):
  ```json
  GET /products/_search
  {
    "query": {
      "multi_match": {
        "query": "wireless headphones",
        "fields": ["description"]
      }
    }
  }
  ```

### **3.2 Filtering with Predicates**
Use Elasticsearch’s `bool` query for complex filters:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "description": "headphones" } }
      ],
      "filter": [
        { "range": { "price": { "gte": 50, "lte": 200 } } },
        { "term": { "category": "electronics" } },
        { "date_range": { "published_date": { "gte": "now-1y" } } }
      ]
    }
  }
}
```

### **3.3 Faceting & Aggregations**
Generate interactive filters dynamically:
```json
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": { "field": "category.keyword" }
    },
    "price_ranges": {
      "histogram": { "field": "price", "interval": 50 }
    }
  }
}
```

**Output Example**:
```json
"aggregations": {
  "categories": {
    "buckets": [
      { "key": "electronics", "doc_count": 120 },
      { "key": "apparel", "doc_count": 85 }
    ]
  }
}
```

### **3.4 Pagination**
- **Offset-Limit**:
  ```json
  GET /products/_search
  {
    "from": 0,
    "size": 10,
    "query": { "match_all": {} }
  }
  ```
- **Cursor-Based** (better for large datasets):
  ```json
  GET /products/_search
  {
    "search_after": [5000, "last_timestamp"],
    "sort": ["_id", "published_at"],
    "size": 10
  }
  ```

### **3.5 Performance Tuning**
| **Optimization**       | **Action**                                                                 |
|-------------------------|----------------------------------------------------------------------------|
| **Indexing**            | Use `keyword` for exact matches, `text` for search.                      |
| **Caching**             | Enable `request_cache` for repeated queries.                              |
| **Relevance Tuning**    | Adjust `boost` or use `function_score` queries.                          |
| **Sharding**            | Distribute indices across nodes for parallel queries.                     |

---

## **4. Query Examples**

### **4.1 Elasticsearch Queries**
**Basic Search + Filters**:
```json
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "query": "laptop" } }
      ],
      "filter": [
        { "term": { "brand": "dell" } },
        { "range": { "price": { "lte": 1500 } } }
      ]
    }
  },
  "aggs": {
    "brands": { "terms": { "field": "brand.keyword" } }
  }
}
```

**Fuzzy Search**:
```json
{
  "query": {
    "fuzzy": { "description": { "value": "wireles headphones", "fuzziness": 2 } }
  }
}
```

### **4.2 GraphQL Filters (Example)**
```graphql
query ProductSearch($searchTerm: String, $minPrice: Float, $maxPrice: Float) {
  products(
    searchTerm: $searchTerm
    filters: {
      price: { gte: $minPrice, lte: $maxPrice }
      category: "electronics"
    }
  ) {
    items {
      id
      name
      price
    }
    facets {
      categories
      priceRanges
    }
  }
}
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **[Pagination](...)**      | Splits large datasets into manageable chunks.                                | When serving >1,000 results per request.   |
| **[Rate Limiting](...)**  | Controls API abuse (e.g., 100 requests/minute).                               | For public-facing search APIs.             |
| **[Caching](...)**        | Stores frequent queries (e.g., Elasticsearch `request_cache`).               | High-traffic search applications.         |
| **[Lazy Loading](...)**   | Loads filters/facets on demand (e.g., AJAX).                                 | Interactive dashboards.                   |
| **[Personalization](...)**| Ranks results by user preferences (e.g., `user_id` boosts).                  | E-commerce or content platforms.          |

---

## **6. Best Practices**
1. **Schema Design**:
   - Use `keyword` for filterable fields (e.g., `category`, `brand`).
   - Normalize nested data (e.g., `properties: { color: "red", size: "M" }`).
2. **Relevance**:
   - Combine `match` (full-text) with `term` (exact) for hybrid searches.
   - Use `function_score` to boost recent/featured items.
3. **UI/UX**:
   - Pre-fetch facets to reduce perceived load time.
   - Provide a "clear all" button for filters.
4. **Monitoring**:
   - Track slow queries in Elasticsearch (`_nodes/stats`).
   - Alert on high `search_shards` usage.

---
**See Also**:
- [Elasticsearch Official Docs](https://www.elastic.co/guide/)
- [GraphQL Filters Guide](https://graphql.org/learn/queries/#filters)