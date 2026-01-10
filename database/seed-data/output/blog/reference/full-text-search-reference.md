# **[Pattern] PostgreSQL Full-Text Search Reference Guide**

---
## **1. Overview**
PostgreSQL’s built-in **Full-Text Search (FTS)** allows efficient semantic searches across unstructured or semi-structured data (e.g., text fields) without requiring external search engines like Elasticsearch. It processes text into **tokens**, applies **stemming** (reducing words to root forms, e.g., "running" → "run"), ignores **stop words** (e.g., "and", "the"), and uses **inverted indexes** for fast querying.

Unlike exact string matching or `LIKE` patterns, FTS prioritizes relevance over exact matches, ranking results by how closely they match the query. This guide covers implementation details, schema design, query syntax, and performance optimizations.

---
## **2. Key Concepts**
| Concept          | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| **tsvector**     | A specialized data type storing parsed/normalized text (e.g., `{running: run}`). |
| **tsquery**      | A query syntax for FTS, combining terms with Boolean operators (`&`, `|`, `!`). |
| **GIN Index**    | An inverted index type for fast `tsvector` lookups.                          |
| **Dictionary**   | Controls tokenization (e.g., stemming, stopword removal).                   |
| **Parser**       | Defines how text is split into tokens (e.g., `simple`, `english`).           |

---
## **3. Schema Reference**
### **3.1 Required Tables**
| Table          | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `documents`    | Stores documents with a `content` field (text) and a `tsvector` column.      |

### **3.2 Column Types**
| Column    | Data Type       | Description                                                                 |
|-----------|-----------------|-----------------------------------------------------------------------------|
| `id`      | `SERIAL`        | Primary key.                                                                |
| `title`   | `VARCHAR`       | Document title.                                                              |
| `content` | `TEXT`          | Unstructured text (will be parsed into `tsvector`).                          |
| `content_ts`| `TSVECTOR`      | Precomputed FTS vector for fast queries (indexed).                          |

### **3.3 Example Schema**
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    content_ts TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', content)
    ) STORED
);

CREATE INDEX idx_documents_content_ts ON documents USING GIN(content_ts);
```

---
## **4. Query Examples**

### **4.1 Basic Search**
```sql
-- Search for documents containing "running" (stemmed to "run")
SELECT * FROM documents
WHERE content_ts @@ to_tsquery('english', 'running');
```
**Output:** Returns documents with text like "running", "runs", or "runner."

---

### **4.2 Boolean Operators**
| Operator | Meaning                          | Example                     |
|----------|----------------------------------|-----------------------------|
| `&`      | AND                              | `to_tsquery('running & jump')` |
| `\`      | NOT                              | `to_tsquery('running \cat')` |
| `!`      | NOT (alias for `\`)              | `to_tsquery('!running')`     |
| `|`      | OR                               | `to_tsquery('running | walk')`  |

**Example:**
```sql
-- Find documents about "running" but not "cat"
SELECT * FROM documents
WHERE content_ts @@ to_tsquery('english', 'running & !cat');
```

---

### **4.3 Weighted Search (Ranking)**
Use `ts_rank()` to return results sorted by relevance:
```sql
SELECT
    title,
    ts_rank(content_ts, to_tsquery('english', 'running')) AS relevance_score
FROM documents
WHERE content_ts @@ to_tsquery('english', 'running')
ORDER BY relevance_score DESC;
```

---

### **4.4 Phrases and Wildcards**
- **Phrase search:** Enclose words in quotes (`"running fast"`).
- **Wildcards:** Use `*` (e.g., `to_tsquery('running*')` matches "running", "run").

```sql
-- Find documents with "running fast" as a phrase
SELECT * FROM documents
WHERE content_ts @@ to_tsquery('english', '"running fast"');
```

---

### **4.5 Custom Dictionaries & Parsers**
Override default behavior (e.g., disable stemming):
```sql
-- Use 'simple' parser (no stemming) for exact matches
SELECT * FROM documents
WHERE content_ts @@ to_tsquery('simple', 'running');
```

---
## **5. Performance Optimization**
| Technique                          | Description                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **GIN Index**                       | Required for fast `tsvector` lookups (created automatically with `GENERATED`). |
| **Partial Indexes**                 | Index only specific columns (e.g., `title_ts`).                              |
| **Avoid `text` in `WHERE`**         | Always use `tsvector` for FTS queries.                                       |
| **Update `tsvector` on Insert/Update** | Use `on commit` triggers if not using `GENERATED`.                          |

---
## **6. Related Patterns**
- **[Indexing Patterns](https://example.com/indexing)**: Use GIN indexes for FTS and JSON data.
- **[Text Search with PostgreSQL](https://www.postgresql.org/docs/current/textsearch.html)**: Official PostgreSQL docs for advanced FTS.
- **[Trigram Search](https://www.postgresql.org/docs/current/textsearch-trgm.html)**: Exact substring matching (e.g., `pg_trgm` extension).
- **[Vector Search](https://www.postgresql.org/docs/current/pgvector.html)**: For embedding-based similarity (PostgreSQL 14+).

---
## **7. Limitations**
- **No fuzzy matching**: Unlike Elasticsearch, PostgreSQL FTS does not support typos (use `pg_trgm` for exact substrings).
- **Scalability**: For >1M rows, consider partitioning or dedicated search solutions.
- **No highlighting**: Postgres FTS lacks built-in term highlighting.

---
## **8. Example: Full Workflow**
1. **Insert data:**
   ```sql
   INSERT INTO documents (title, content)
   VALUES ('Guide', 'Running in the park is fun!');
   ```
2. **Search:**
   ```sql
   SELECT * FROM documents
   WHERE content_ts @@ to_tsquery('english', 'run');
   ```
3. **Optimize:**
   ```sql
   CREATE INDEX idx_content_ts ON documents (content_ts);
   ```

---
**Next Steps:**
- Explore `ts_stat()` for statistics and tuning.
- Combine FTS with `JSONB` for hybrid searches.