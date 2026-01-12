---
# **[Pattern] Elasticsearch Database Patterns Reference Guide**

---

## **1. Overview**
Elasticsearch Database Patterns provide structured approaches for modeling, indexing, querying, and maintaining data in Elasticsearch to optimize performance, scalability, and maintainability. Unlike traditional relational database patterns, Elasticsearch leverages its distributed, full-text search, and analytical capabilities to handle unstructured or semi-structured data efficiently. This reference guide covers foundational patterns like **Single-Index vs. Multi-Index**, **Nested vs. Joined Objects**, **Time-Series Indexing**, and **Log Aggregation**, along with implementation details, best practices, and anti-patterns.

---

## **2. Schema Reference**
Elasticsearch schemas differ from relational databases; they rely on **mappings**, **indexing strategies**, and **document structures**. Below are common schema patterns and their configurations.

| **Pattern**               | **Use Case**                          | **Mapping Example**                                                                 | **Key Considerations**                                                                 |
|---------------------------|---------------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Single-Index**          | Simple data with uniform queries.     | `index: "products"`<br>`mapping: {<br>`   "properties": {<br>`     "name": { "type": "text" },<br>`     "price": { "type": "float" },<br>`     "tags": { "type": "keyword" }<br>`   }<br>`}` | Single index simplifies queries but may lead to large shard sizes. Use for low-cardinality data. |
| **Multi-Index**           | Separate concerns (e.g., users vs. orders). | `index: ["users", "orders"]`<br>`Mappings vary per index.`                     | Improves performance and management but increases complexity. Use for high-cardinality data. |
| **Nested Objects**        | One-to-many relationships (e.g., orders with line items). | `"line_items": { "type": "nested", "properties": {...} }`                          | Enables queries across nested fields but impacts performance (avoid deep nesting).     |
| **Joined Objects**        | Many-to-many or complex relationships. | `"aliases": { "type": "join", "relations": { "user": "alias" } }`                | Use for sparse data to save space; requires explicit joins in queries.               |
| **Time-Series Index**     | Time-bound data (e.g., logs, metrics). | `index: "logs-2023-10-*"`<br>`"date": { "type": "date" }`                          | Optimized for time-based queries; use aliases for rolling indices.                     |
| **Log Aggregation**       | Consolidating logs from multiple sources. | `"source": "text", "timestamp": "date"`<br>+ Ingest pipelines for preprocessing.   | Preprocess logs (e.g., extract fields) to reduce index size and improve query speed.   |

---

## **3. Implementation Details**
### **3.1 Indexing Strategies**
- **Index Aliases**: Use for zero-downtime reindexing or time-series data.
  ```json
  PUT /logs@current
  POST /logs@current/_alias/logs
  ```
- **Index Templates**: Define default mappings for dynamic indices.
  ```json
  PUT /_index_template/logs_template
  {
    "index_patterns": ["logs-*"], "template": { ... }
  }
  ```
- **Sharding**: Distribute data across nodes (default: 5 primary, 1 replica).
  ```json
  PUT /my_index
  {
    "settings": { "number_of_shards": 3, "number_of_replicas": 1 }
  }
  ```

### **3.2 Query Patterns**
#### **Basic Queries**
| **Query Type**            | **Use Case**                          | **Example**                                                                 |
|---------------------------|---------------------------------------|----------------------------------------------------------------------------|
| **Term Query**            | Exact matches (e.g., `status: "active"`). | `{ "term": { "tags.keyword": "premium" } }`                               |
| **Match Query**           | Full-text search (analyzed fields).   | `{ "match": { "description": "wireless headphones" } }`                   |
| **Range Query**           | Numeric/date ranges.                  | `{ "range": { "price": { "gte": 100, "lte": 500 } } }`                   |
| **Bool Query**            | Composite conditions.                 | `{ "bool": { "must": [...], "filter": [...] } }`                           |

#### **Advanced Queries**
- **Nested Queries**: Query nested objects.
  ```json
  {
    "query": {
      "nested": {
        "path": "line_items",
        "query": { "match": { "line_items.product": "laptop" } }
      }
    }
  }
  ```
- **Aggregations**: Analyze data (e.g., stats, histograms).
  ```json
  {
    "aggs": {
      "avg_price": { "avg": { "field": "price" } },
      "price_range": { "histogram": { "field": "price", "interval": 100 } }
    }
  }
  ```
- **Scripted Fields**: Dynamic calculations (e.g., discounts).
  ```json
  {
    "script_fields": {
      "final_price": { "script": "params.base_price * (1 - params.discount)" }
    }
  }
  ```

### **3.3 Best Practices**
- **Avoid Wildcard Indices**: Use explicit index names (e.g., `logs-2023-10`).
- **Limit Field Mappings**: Reduce index size; use `keyword` for exact matches.
- **Use ILM (Index Lifecycle Management)**: Automate index rollover/compression.
  ```json
  PUT /_ilm/policy/logs_policy
  { "policy": { "phases": { ... } } }
  ```
- **Leverage Caching**: Enable request/filter caching for repeated queries.

### **3.4 Common Pitfalls**
- **Shard Size**: Keep shards <50GB to avoid performance issues.
- **Over-Indexing**: Avoid indexing raw logs; preprocess data.
- **Nested Abuse**: Nested objects slow down queries; prefer denormalization.
- **No Replicas**: Always set replicas (>0) for fault tolerance.

---

## **4. Query Examples**
### **4.1 Single-Index Example**
**Index**: `products`
**Query**: Find products tagged "sale" with price < $100.
```json
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "tags": "sale" } },
        { "range": { "price": { "lt": 100 } } }
      ]
    }
  }
}
```

### **4.2 Multi-Index Example**
**Indices**: `users`, `orders`
**Query**: Find users who placed orders in the last 30 days.
```json
GET /_search
{
  "query": {
    "bool": {
      "filter": [
        { "range": { "orders.timestamp": { "gte": "now-30d" } } },
        { "has_parent": { "parent_type": "user", "query": { ... } } }
      ]
    }
  }
}
```

### **4.3 Time-Series Example**
**Index**: `app_metrics-2023-10-01`
**Query**: Average CPU usage over the last hour.
```json
GET /app_metrics-2023-10-*/_search
{
  "size": 0,
  "aggs": {
    "avg_cpu": { "avg": { "field": "cpu.usage" } }
  }
}
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Pipelines]**           | Process documents on ingest (e.g., log parsing, enrichments).                  | When raw data requires transformation before indexing.                          |
| **[Cross-Cluster Search]** | Query multiple Elasticsearch clusters simultaneously.                           | For federated search across distributed environments.                           |
| **[Geospatial Queries]**  | Location-based searches (e.g., "nearby restaurants").                          | Applications requiring proximity or geographic filters.                         |
| **[Machine Learning]**    | Anomaly detection or time-series forecasting.                                  | For predictive analytics on indexed data.                                       |
| **[Security Patterns]**   | Role-based access control (RBAC) or field-level security.                      | Multi-tenant applications with sensitive data.                                 |

---

## **6. Further Reading**
- [Elasticsearch Official Docs: Indexing](https://www.elastic.co/guide/en/elasticsearch/reference/current/indexing.html)
- *Elasticsearch: The Definitive Guide* (O’Reilly) – Chapter 7 (Designing for Performance).
- [Kibana Dev Tools](https://www.elastic.co/guide/en/kibana/current/dev-tools.html) – Interactive query testing.

---
**Note**: Adjust shard/replica counts based on cluster size. Monitor with [Elasticsearch APIs](https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-stats.html).