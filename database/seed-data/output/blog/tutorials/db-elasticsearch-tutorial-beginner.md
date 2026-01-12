```markdown
# Elasticsearch Database Patterns: Search, Not Just Storage

![Elasticsearch Logo](https://www.elastic.co/images/elasticsearch-logo-white.png)
*Building scalable search systems that actually work (not just "store everything here")*

---

## Introduction: When Your Database Becomes a Search Nightmare

Modern applications increasingly rely on search functionality—whether it's a product catalog, news feed, or user-generated content. For many developers, a relational database (RDBMS) like PostgreSQL or MySQL was once enough. But as data scales and users demand faster, more flexible search results, these systems often hit walls:

- **Slow full-text search**: RDBMS full-text indexes struggle with large datasets and complex queries.
- **Fixed schemas**: Adding new searchable fields without migrations becomes painful.
- **Aggregations are painful**: Counting, filtering, and grouping become heavyweight operations.

This is where Elasticsearch (or other search engines) shines—but **without proper design patterns**, you’ll end up with a bloated, inefficient search layer that feels like a hack. This guide will help you build elasticsearch integrations that are *scalable*, *maintainable*, and *performant*—not just "works for now."

---

## The Problem: When Elasticsearch Becomes a Data Graveyard

Elasticsearch is a powerful search engine, but it’s **not a replacement for your database**. Many teams fall into these traps:

### 1. **Dumping Raw Data Without Structure**
Storing entire database records (e.g., user profiles, orders) in Elasticsearch as JSON blobs leads to:
- **Bloat**: Elasticsearch indices grow unwieldy with duplicate or irrelevant fields.
- **Querying nightmare**: Mixing metadata with searchable fields makes indexing and querying messy.
- **Atomicity issues**: If your database deletes a record, Elasticsearch might still have stale data.

#### Example of *bad* schema design:
```json
// Indexed as-is from the database:
{
  "id": 123,
  "name": "Widget X",
  "price": 29.99,
  "created_at": "2023-01-01",
  "user_ratings": [4, 5, 3, 4],
  "user_metadata": { "premium": true, "tags": ["widget", "blue"] }
}
```
**Problem**: How do you efficiently search by `user_ratings` (array) or `user_metadata.tags` (nested object)?

---

### 2. **Ignoring Indexing Patterns**
Without thoughtful indexing, even simple searches become slow. Common anti-patterns:
- **No aliasing**: Downtime during reindexing because you can’t switch indices.
- **Over-indexing**: Storing every field you’ll *might* search for (wasting space and slowing writes).
- **Static mappings**: Adding new searchable fields requires reindexing the entire dataset.

---

### 3. **Tight Coupling with Backend Logic**
If your search queries are hardcoded in your application (e.g., `GET /products?filter=foo`), scaling becomes difficult. You lose flexibility to:
- Change search logic without deploying code.
- Optimize queries at the Elasticsearch level (e.g., using `filter` contexts for caching).

---

## The Solution: Elasticsearch Database Patterns

The key to success is treating Elasticsearch as a **dedicated search layer**—not a dumping ground. Here’s how:

### 1. **Design for Search, Not Storage**
Elasticsearch excels at:
- Full-text search (fuzzy matching, highlighting, synonyms).
- Aggregations (grouping, stats, top-hits).
- Geospatial queries.

**But** it’s terrible at:
- Transactions (ACID guarantees).
- Complex joins (though `parent-child` relationships help).
- Exact integer/date comparisons (use `filter` contexts instead of `query`).

**Rule of thumb**: If you can’t express it in Elasticsearch’s DSL, it’s probably not the right tool.

---

### 2. **Proper Data Modeling**
Elasticsearch uses **mappings** (schema definitions) to optimize indexing. Poor mappings lead to:
- Slow queries (`"no_mappings"` errors).
- High storage costs (wrong field types).
- Bad relevance scoring.

#### Example of *good* schema design:
For an e-commerce product search, we’d index these fields:
```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },        // Exact matches (e.g., filters)
      "name": { "type": "text", "analyzer": "autocomplete" },  // Full-text search
      "price": { "type": "float" },        // Numeric range queries
      "category": { "type": "keyword" },   // Faceted search
      "description": { "type": "text" },   // Full-text
      "tags": { "type": "keyword" },       // For faceted filters
      "ratings": {                        // Aggregation-friendly
        "type": "integer"
      }
    }
  }
}
```

**Key takeaways**:
- Use `text` for searchable fields (analyzed).
- Use `keyword` for exact matches (e.g., IDs, filters).
- Avoid `object`/`nested` unless you need hierarchical data.

---

### 3. **Separation of Concerns**
Elasticsearch should **only** store data needed for search. For example:
- **Do index**: `name`, `description`, `category`, `tags`.
- **Don’t index**: `user_id`, `created_at` (unless used in filters), or private fields.

---

### 4. **Use Aliases for Zero-Downtime Reindexing**
Aliases let you switch indices without downtime. Example workflow:
1. Create a new index with updated mappings.
2. Reindex data from the old index.
3. Redirect traffic to the new index via alias.

#### Example in Python (using `elasticsearch` library):
```python
from elasticsearch import Elasticsearch

es = Elasticsearch()

# Step 1: Create new index
new_index = "products_v2"
es.indices.create(index=new_index, body={
    "settings": {"number_of_shards": 3},
    "mappings": { "properties": { /* new schema */ } }
})

# Step 2: Reindex data
es.reindex(
    body={
        "source": {"index": "products_v1"},
        "dest": {"index": new_index}
    }
)

# Step 3: Switch alias
es.indices.put_alias(index=new_index, name="products")
es.indices.delete_alias(index="products_v1", name="products")
```

---

### 5. **Optimize Queries with Filter Contexts**
Elasticsearch caches `filter` contexts (unlike `query` contexts, which score documents). Use `filter` for:
- Exact matches (IDs, category filters).
- Range queries (price, date).
- Terms lookups (tags, attributes).

#### Example: Efficient search with filters
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "description": "wireless headphones" } }  // Scored (text field)
      ],
      "filter": [
        { "range": { "price": { "gte": 50 } } },              // Filter (cached)
        { "terms": { "category": ["electronics", "audio"] } }  // Filter (cached)
      ]
    }
  }
}
```

---

## Implementation Guide: Step-by-Step

### Step 1: Define Your Search Requirements
Ask:
1. What will users search for? (Full text vs. exact matches).
2. What aggregations/facets are needed? (e.g., "show me products by price range").
3. How often does the data change? (Real-time vs. near-real-time).

---

### Step 2: Design Your Index Schema
Use `Put Mapping` to set up fields correctly. Example:
```sql
-- Create index with optimized mappings
PUT /products
{
  "settings": {
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": {
        "type": "text",
        "analyzer": "english"
      },
      "price": { "type": "float" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "description": { "type": "text" },
      "in_stock": { "type": "boolean" }
    }
  }
}
```

---

### Step 3: Index Data Efficiently
Avoid indexing unnecessary fields. Example (Python):
```python
from elasticsearch import Elasticsearch

es = Elasticsearch()

product = {
    "id": "123",
    "name": "Wireless Headphones",
    "price": 99.99,
    "category": "electronics",
    "tags": ["audio", "wireless", "bluetooth"],
    "description": "Noise-cancelling wireless headphones with 30hr battery.",
    "in_stock": True
}

# Index only search-relevant fields
es.index(index="products", id=product["id"], body={
    "name": product["name"],
    "description": product["description"],
    "category": product["category"],
    "tags": product["tags"],
    "price": product["price"],
    "in_stock": product["in_stock"]
})
```

---

### Step 4: Build a Query DSL
Use the [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html) for flexible searches. Example:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "headphones" } },
        { "match": { "description": "wireless" } }
      ],
      "filter": [
        { "term": { "category": "electronics" } },
        { "range": { "price": { "lte": 150 } } },
        { "term": { "in_stock": true } }
      ]
    }
  },
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 50 },
          { "from": 50, "to": 100 },
          { "from": 100 }
        ]
      }
    }
  }
}
```

---

### Step 5: Handle Updates and Deletes
Elasticsearch supports partial updates but not native deletes (use `delete_by_query` carefully):
```python
# Update a product's price
es.update(index="products", id="123", body={
    "doc": { "price": 79.99 }
})

# Delete products out of stock (use with caution!)
es.delete_by_query(index="products", body={
    "query": { "bool": { "must_not": { "term": { "in_stock": true } } } }
})
```

---

### Step 6: Implement Near-Real-Time Sync
Elasticsearch isn’t immediately updated. Use:
- **Bulk API**: Batch updates for efficiency.
- **Async workers**: Decouple writes (e.g., RabbitMQ + Celery).
- **Retry logic**: Handle failed reindexes.

Example bulk update:
```python
actions = [
    {
        "_op_type": "update",
        "_index": "products",
        "_id": "123",
        "doc": { "price": 79.99 }
    },
    {
        "_op_type": "update",
        "_index": "products",
        "_id": "456",
        "doc": { "in_stock": False }
    }
]

es.bulk(index="products", body="\n".join([json.dumps(action) for action in actions]))
```

---

## Common Mistakes to Avoid

### 1. **Over-Indexing**
- **Mistake**: Indexing every field from your database.
- **Fix**: Only include fields needed for search/aggregations.
- **Example**: If you don’t search by `user_id`, don’t index it.

### 2. **Ignoring Field Types**
- **Mistake**: Using `text` for IDs or `keyword` for ranges.
- **Fix**:
  - `keyword` for exact matches (IDs, categories).
  - `text` for full-text search (descriptions, names).
  - `float`/`integer` for numeric ranges.

### 3. **No Aliases for Reindexing**
- **Mistake**: Changing mappings requires downtime.
- **Fix**: Use aliases to switch indices without interruption.

### 4. **Tight Coupling with Backend**
- **Mistake**: Hardcoding search logic in your app.
- **Fix**: Move complex queries to Elasticsearch (e.g., use `painless` scripts for custom logic).

### 5. **Forgetting to Optimize Aggregations**
- **Mistake**: Running aggregations on large datasets without limits.
- **Fix**: Use `size` to cap results:
  ```json
  {
    "aggs": {
      "categories": {
        "terms": { "field": "category", "size": 10 }
      }
    }
  }
  ```

### 6. **No Monitoring**
- **Mistake**: Ignoring slow queries or high disk usage.
- **Fix**: Use Elasticsearch’s [Monitoring API](https://www.elastic.co/guide/en/elasticsearch/reference/current/monitoring.html) and tools like Kibana.

---

## Key Takeaways

✅ **Elasticsearch is for search, not storage** – Design mappings for querying, not denormalization.
✅ **Use `keyword` for exact matches, `text` for full-text** – Wrong types = slow queries.
✅ **Separate search data from your database** – Avoid replication lag and consistency issues.
✅ **Leverage `filter` contexts** – They’re cached and faster than `query` contexts.
✅ **Plan for reindexing with aliases** – Zero-downtime updates are critical.
✅ **Optimize aggregations** – Limit `size` and use `composition` for complex hierarchies.
✅ **Monitor performance** – Slow queries kill scalability.
❌ **Don’t dump raw DB records** – Elasticsearch isn’t a backup or ORM replacement.
❌ **Avoid over-faceting** – Too many aggregations slow down queries.
❌ **Ignore updates/deletes** – Use `delete_by_query` sparingly and test thoroughly.

---

## Conclusion: Build for Scale from Day One

Elasticsearch is a game-changer for search, but **design matters**. By treating it as a dedicated layer—with proper indexing, querying patterns, and synchronization—you’ll build systems that scale without pain. Start small, test aggressively, and iterate. And remember: *There’s no "set it and forget it" with Elasticsearch.*

### Next Steps:
1. Experiment with the [Elasticsearch Sandbox](https://www.elastic.co/elasticsearch/sandbox/).
2. Bookmark the [Query DSL Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html).
3. Try reindexing your dev data with aliases—it’s safer than you think!

Happy searching! 🚀
```