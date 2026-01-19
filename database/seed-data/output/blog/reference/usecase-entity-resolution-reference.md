# **[Pattern] Entity Resolution Patterns Reference Guide**

## **Overview**
Entity resolution refers to the process of matching and linking records that describe the same real-world entity across different datasets or systems. This pattern provides proven approaches to resolving inconsistencies in data, such as duplicates, missing values, or naming variations, ensuring data integrity and consistency. Common use cases include deduplication, data cleansing, and entity linking in databases, ETL pipelines, and analytical systems.

---

## **Key Concepts**
Before implementing, understand these core terms:

| **Term**               | **Definition**                                                                                     |
|------------------------|--------------------------------------------------------------------------------------------------|
| **Exact Matching**     | Records match exactly (e.g., same ID, name, and attributes).                                     |
| **Fuzzy Matching**     | Records match based on similarity (e.g., partial name matches, typos).                          |
| **Key-Based Matching** | Uses predefined fields (e.g., email, SSN) to resolve entities.                                  |
| **Graph-Based Matching**| Leverages relationships between entities (e.g., co-occurrence, clustering) for resolution. |
| **Block Matching**     | Groups potential matches based on fields (e.g., first name + last name) before pairwise comparison. |
| **Thresholding**       | Defines similarity scores (e.g., 90% match) to classify records as "likely matches."            |
| **Blocking Key**       | A subset of attributes used to filter candidate pairs (e.g., first 3 letters of last name).    |

---

## **Schema Reference**
The following schema outlines a typical entity resolution table structure:

| **Field**               | **Type**       | **Description**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `entity_id`             | `UUID`         | Unique identifier for the resolved entity.                                                          |
| `source_entity_id`      | `UUID`         | Original ID from source system.                                                                    |
| `source_system`         | `String`       | Name of the source system (e.g., `CRM`, `ERP`).                                                   |
| `match_score`           | `Float (0-1)`  | Similarity score between records (e.g., 0.95).                                                   |
| `resolution_method`     | `Enum`         | How the match was resolved (`exact`, `fuzzy`, `graph`, `rule-based`).                              |
| `confidence`            | `String`       | Confidence label (`high`, `medium`, `low`).                                                       |
| `merged_attributes`     | `JSON`         | Consolidated fields from all matched records.                                                      |
| `resolved_at`           | `Timestamp`    | When the resolution was finalized.                                                                 |
| `blocking_key`          | `String`       | Aggregation key used for candidate generation (e.g., `last_name_prefix`).                        |

**Example Table:**
```sql
CREATE TABLE entity_resolution (
    entity_id UUID PRIMARY KEY,
    source_entity_id UUID,
    source_system VARCHAR(50),
    match_score FLOAT,
    resolution_method VARCHAR(20),
    confidence VARCHAR(10),
    merged_attributes JSONB,
    resolved_at TIMESTAMP,
    blocking_key VARCHAR(100)
);
```

---

## **Implementation Patterns**

### **1. Exact Matching**
Use when records have unique identifiers (e.g., `email`, `SSN`).
**Rule:**
```sql
-- SQL Example: Resolve by exact email match
SELECT a.entity_id, b.entity_id AS duplicate_id
FROM entities a
JOIN entities b ON a.email = b.email AND a.entity_id != b.entity_id;
```

### **2. Fuzzy Matching**
Apply string similarity algorithms (e.g., Levenshtein, Jaro-Winkler) for near-matches.
**Tools/Libraries:**
- Python: `fuzzywuzzy`, `rapidfuzz`
- Java: `Apache Commons Text` (for edit distance)
- SQL: `pg_trgm` (PostgreSQL) or `SOUNDEX` (MySQL).

**Example (Python with `fuzzywuzzy`):**
```python
from fuzzywuzzy import fuzz

def is_match(record1, record2):
    ratio = fuzz.ratio(record1["name"], record2["name"])
    return ratio > 90  # Threshold

matches = [
    (r1, r2) for r1 in records if any(is_match(r1, r2) for r2 in records if r1 != r2)
]
```

### **3. Blocking + Pairwise Comparison**
Efficiently reduce candidate pairs before scoring.
**Steps:**
1. **Block by Key:** Group records by a substring of a field (e.g., first 3 letters of `last_name`).
2. **Compare Within Blocks:** Apply fuzzy matching only to candidates in the same block.

**SQL Example:**
```sql
-- Blocking by last name prefix
WITH name_blocks AS (
    SELECT
        entity_id,
        substring(last_name, 1, 3) AS block_key
    FROM entities
)
SELECT
    a.entity_id, b.entity_id,
    fuzz.ratio(a.name, b.name) AS similarity
FROM name_blocks a
JOIN name_blocks b ON a.block_key = b.block_key AND a.entity_id < b.entity_id
WHERE fuzz.ratio(a.name, b.name) > 85;
```

### **4. Graph-Based Matching**
Useful for linked data (e.g., social networks, supply chains).
**Approach:**
- Treat entities as nodes and relationships as edges.
- Apply clustering algorithms (e.g., Louvain) to group similar nodes.

**Example (NetworkX in Python):**
```python
import networkx as nx

G = nx.Graph()
for record in records:
    G.add_node(record["id"], **record)

# Add edges based on similarity
for i, r1 in enumerate(records):
    for j, r2 in enumerate(records[i+1:], i+1):
        if is_match(r1, r2):
            G.add_edge(r1["id"], r2["id"])

# Cluster nodes
clusters = list(nx.connected_components(G))
```

### **5. Rule-Based Matching**
Define custom rules (e.g., "If `phone` starts with `+1` and `country = USA`, resolve").
**Example (SQL with CASE):**
```sql
SELECT
    a.entity_id, b.entity_id,
    CASE
        WHEN a.country = b.country AND LEFT(a.phone, 2) = LEFT(b.phone, 2) THEN 1
        ELSE 0
    END AS match_flag
FROM entities a
JOIN entities b ON a.country = b.country;
```

---

## **Query Examples**

### **Query 1: Find Potential Duplicates by Name**
```sql
-- PostgreSQL with pg_trgm
SELECT
    a.entity_id AS id1,
    b.entity_id AS id2,
    similarity(a.name, b.name) AS similarity_score
FROM entities a
JOIN entities b ON a.entity_id < b.entity_id
WHERE a.name % b.name  -- Trigram similarity
GROUP BY a.entity_id, b.entity_id
HAVING similarity(a.name, b.name) > 0.8;
```

### **Query 2: Resolve Entities with High Confidence**
```sql
-- Filter high-confidence matches (score > 0.95)
SELECT *
FROM entity_resolution
WHERE match_score > 0.95
ORDER BY match_score DESC;
```

### **Query 3: Merge Attributes for Resolved Entities**
```sql
-- Update merged_attributes in-place
UPDATE entity_resolution er
SET merged_attributes = (
    SELECT jsonb_agg(TO_JSONB(e))
    FROM entities e
    WHERE e.entity_id IN (
        SELECT source_entity_id FROM entity_resolution WHERE entity_id = er.entity_id
    )
)
WHERE er.resolution_method = 'fuzzy';
```

---

## **Performance Considerations**
| **Technique**          | **Pros**                                  | **Cons**                                  | **Best For**                  |
|------------------------|-------------------------------------------|-------------------------------------------|-------------------------------|
| **Exact Matching**     | Fast, deterministic.                       | Limited to exact IDs.                    | CRMs, databases with keys.     |
| **Fuzzy Matching**     | Handles typos/variations.                 | Computationally expensive.                | Large datasets with noise.    |
| **Blocking**           | Reduces candidate pairs.                   | Requires careful key selection.           | High-volume data.             |
| **Graph-Based**        | Captures relationships.                    | Complex setup.                           | Linked data (e.g., graphs).   |
| **Rule-Based**         | Customizable logic.                       | Hard to scale.                            | Domain-specific rules.        |

---

## **Related Patterns**
1. **[Data Cleansing]**
   - Standardizes formats (e.g., `123-456-7890` → `1234567890`) before resolution.
2. **[Data Profiling]**
   - Analyzes data distributions to identify resolution challenges (e.g., missing fields).
3. **[Change Data Capture (CDC)]**
   - Streams new/updated records for real-time resolution.
4. **[Master Data Management (MDM)]**
   - Centralizes entity resolution at scale (e.g., SAP MDG, Informatica MDM).
5. **[Feature Stores]**
   - Stores precomputed similarity features (e.g., embeddings) for faster matching.

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                                  | **Link**                                  |
|------------------------|---------------------------------------------|-------------------------------------------|
| **Apache Spark**       | Large-scale fuzzy matching (NLP & graph).   | [spark.apache.org](https://spark.apache.org/) |
| **Talend/OpenRefine**  | Interactive data cleanup/resolution.        | [openrefine.org](https://openrefine.org/) |
| **Diffbot**            | AI-powered entity resolution APIs.          | [diffbot.com](https://www.diffbot.com/)   |
| **FLink**              | Scalable entity resolution framework.       | [f-link.io](https://f-link.io/)           |

---
## **Troubleshooting**
| **Issue**               | **Diagnosis**                                  | **Solution**                              |
|-------------------------|-----------------------------------------------|-------------------------------------------|
| **High False Positives**| Threshold too low.                            | Increase similarity threshold.           |
| **Slow Performance**    | No blocking or inefficient joins.            | Add blocking keys or optimize queries.   |
| **Incomplete Matches**  | Missing critical fields (e.g., dates).       | Add more attributes to blocking keys.    |
| **Graph Overload**      | Too many edges in graph.                     | Use approximate algorithms (e.g., Locality-Sensitive Hashing). |

---
## **Example Workflow**
1. **Preprocess Data:**
   - Clean text (lowercase, remove accents) using `nltk` or `spaCy`.
   - Standardize formats (dates, phone numbers).

2. **Block Candidates:**
   ```python
   from collections import defaultdict
   blocks = defaultdict(list)
   for record in records:
       key = record["last_name"][:3].lower()
       blocks[key].append(record)
   ```

3. **Score Pairs:**
   Use `fuzzywuzzy` or `rapidfuzz` to compare records within each block.

4. **Merge Resolved Entities:**
   ```sql
   INSERT INTO entity_resolution (entity_id, source_entity_id, match_score)
   SELECT
       NEWID() AS entity_id,
       a.entity_id,
       similarity_score
   FROM matched_pairs a;
   ```

5. **Post-Process:**
   - Validate merges with domain experts.
   - Update source systems via APIs or ETL.

---
## **Security Considerations**
- **Data Privacy:** Anonymize PII before matching (e.g., hash emails).
- **Audit Logs:** Track resolution actions for compliance (GDPR, HIPAA).
- **Access Control:** Restrict resolution tools to authorized users.