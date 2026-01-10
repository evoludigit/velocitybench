```markdown
# **Full-Text Search in PostgreSQL: A Practical Guide to Building Powerful Search Without Elasticsearch**

![PostgreSQL FTS Illustration](https://www.postgresql.org/media/img/about/images/press/pics/postgresql-logo.svg)

As a backend developer, you’ve probably encountered the challenge of implementing **search functionality** that feels intuitive—where users can type a query like *"fast running shoes"* and get results like **"Nike Air Zoom Pegasus"**, even though the actual text might contain **"running machines"** or **"sneakers"**.

By default, most databases—including PostgreSQL—offer **LIKE-based searches**, which are slow, inflexible, and fail to deliver meaningful results. This is where **full-text search (FTS)** comes in.

PostgreSQL’s built-in FTS engine is a hidden powerhouse. It **tokensizes text, applies stemming, filters stop words, and ranks results by relevance**—all without requiring an external search engine like Elasticsearch. But FTS isn’t just about performance; it’s about **semantic understanding**.

In this post, we’ll explore:
- How FTS works under the hood
- Why `LIKE '%term%'` is a terrible search strategy
- How to implement **ranked, efficient FTS** in PostgreSQL
- Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why `LIKE` is Broken for Search**

Suppose you’re building an e-commerce platform with a product table that includes a `description` column. If users want to find products like *"running shoes"*, you might try:

```sql
SELECT *
FROM products
WHERE description LIKE '%running shoes%';
```

Sounds simple—but this approach is **fundamentally flawed**:

1. **No Index Utilization**
   PostgreSQL **cannot** use an index on `description` because `LIKE '%term%'` requires a **full table scan**. On large datasets, this becomes excruciatingly slow.

2. **Case Sensitivity & Exact Matching**
   - `"Running"` ≠ `"running"` unless you add `ILIKE`.
   - Neither `"running"` nor `"shoes"` will match `"fast running sneakers"`.

3. **No Stemming (Morphological Analysis)**
   - `"running"` ≠ `"run"` ≠ `"runs"`
   - `"better"` ≠ `"best"` ≠ `"improved"`

4. **Stop Word Ignorance**
   - `"the"` and `"and"` are ignored in FTS (by default), but not in `LIKE`-based searches. This means queries like `"shoes for running"` may miss relevant results if stop words break the pattern.

5. **No Relevance Ranking**
   You can’t sort results by **how well** they match the query. Do you want **"running shoes"** first, or **"sneakers for jogging"**?

6. **No Synonym Handling**
   If a user searches for `"sneakers"`, should it match `"running shoes"`? FTS alone won’t do this—you’ll need to extend it with **custom dictionaries**.

7. **Performance Degradation with Large Text Fields**
   `LIKE` on `TEXT` columns forces **blocked scans**, hurting performance as your dataset grows.

### **A Real-World Example**
Imagine a blog platform where users search for articles about **"modern web development"**. With `LIKE`, you might get:
- ✅ `"Modern Web Development in 2024"` (exact match)
- ❌ `"Building Scala Microservices"` (missed because of stop words)
- ❌ `"The Future of Backend Engineering"` (missed because of stemming)

FTS solves all these issues—**without** requiring a separate search service.

---

## **The Solution: PostgreSQL Full-Text Search**

PostgreSQL’s FTS system works by:
1. **Tokenizing** text into words (removing punctuation, splitting contractions).
2. **Stemming** words to their base form (`running` → `run`).
3. **Filtering stop words** (`the`, `and`, `is`).
4. **Building an inverted index** (via `GIN`) for fast lookups.
5. **Ranking results** by relevance (using `ts_rank`).

### **Core Components**
| Component       | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| **`tsvector`**  | Storage format for processed (tokenized/stemmed) text.                  |
| **`tsquery`**   | Representation of a user’s search query (supports operators like `&`, `|`, `!`). |
| **`GIN` index** | Inverted index for fast FTS searches (enables ranking).                 |

---

## **Implementation Guide: Step-by-Step**

### **1. Setting Up Your Table**
First, let’s define a table with a `description` column and add FTS support.

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    -- Add a tsvector column for FTS
    description_search tsvector
);
```

### **2. Populating the Table**
We’ll insert some sample data:

```sql
INSERT INTO products (name, description) VALUES
    ('Nike Air Zoom Pegasus', 'Fast running shoes for long distance jogging'),
    ('Adidas Ultraboost', 'Lightweight sneakers with excellent cushioning'),
    ('Salomon Speedcross', 'Technical trail running shoes for off-road'),
    ('New Balance 880v11', 'Comfortable running shoes for daily workouts'),
    ('Under Armour HOVR', 'High-performance shoes for sprint training');
```

### **3. Creating a Trigger to Update `tsvector`**
Whenever `description` changes, we’ll update the `tsvector`:

```sql
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.description_search :=
        to_tsvector('english', COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_product_search
BEFORE INSERT OR UPDATE OF description ON products
FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

**Why `COALESCE`?**
If `description` is `NULL`, we still want a valid `tsvector` (empty string becomes an empty vector).

### **4. Creating a GIN Index**
This index enables fast FTS searches:

```sql
CREATE INDEX idx_products_search ON products USING GIN(description_search);
```

### **5. Searching with `ts_query`**
Now, let’s search for products containing `"running"`:

```sql
SELECT id, name, description
FROM products
WHERE description_search @@ to_tsquery('english', 'running');
```

**Results:**
- ✅ Nike Air Zoom Pegasus (`running`)
- ✅ Salomon Speedcross (`running`)
- ❌ Adidas Ultraboost (no `running` mention)

### **6. Handling Multiple Search Terms**
To find products with **both** `"shoes"` and `"fast"`:

```sql
SELECT id, name, description
FROM products
WHERE description_search @@ to_tsquery('english', 'fast & shoes');
```

**Results:**
- ✅ Nike Air Zoom Pegasus (`fast running shoes`)

### **7. Ranking by Relevance**
By default, results are sorted by **coverage** (how many terms match). To get **relevance-based ranking**, use `ts_rank`:

```sql
SELECT
    id,
    name,
    description,
    ts_rank(description_search, to_tsquery('english', 'running')) AS relevance
FROM products
WHERE description_search @@ to_tsquery('english', 'running')
ORDER BY relevance DESC;
```

**Output:**
| id  | name                     | relevance |
|-----|--------------------------|-----------|
| 1   | Nike Air Zoom Pegasus    | 0.45      |
| 3   | Salomon Speedcross       | 0.30      |

### **8. Excluding Terms with `!`**
To find shoes **but not** `"trail"`:

```sql
SELECT id, name
FROM products
WHERE description_search @@ to_tsquery('english', 'shoe !trail');
```

**Results:**
- ✅ Nike Air Zoom Pegasus
- ✅ Adidas Ultraboost
- ❌ Salomon Speedcross (contains `trail`)

### **9. Using Custom Dictionaries (Synonyms)**
PostgreSQL supports **custom word lists** for synonyms. For example, let’s define a mapping where `"sneakers" = "shoes"`:

```sql
CREATE TEXT SEARCH CONFIGURATION sneaker_synonyms (COPY = english);

-- Add synonyms to the config
SELECT setweight(to_regconfig('sneaker_synonyms'), 'A', 1);
SELECT setweight(to_regconfig('sneaker_synonyms'), 'B', 1);

-- Define synonyms
CREATE TEXT SEARCH DICTIONARY sneaker_dict (TEMPLATE = snowball, STOPWORDS = english);
ALTER TEXT SEARCH CONFIGURATION sneaker_synonyms ADD MAPPING FOR asciiword, sneaker_dict;

-- Now, update the products table to use this config
ALTER TABLE products ALTER COLUMN description_search TYPE tsvector USING to_tsvector('sneaker_synonyms', description);
```

Now, searching for `"sneakers"` will also match `"shoes"`:

```sql
SELECT id, name
FROM products
WHERE description_search @@ to_tsquery('sneaker_synonyms', 'sneakers');
```

### **10. Using `websearch_to_tsquery` for Phrases**
If you want to find **exact phrases** (like `"fast running shoes"`), use:

```sql
SELECT id, name
FROM products
WHERE description_search @@ websearch_to_tsquery('english', 'fast running shoes');
```

This ensures the **exact phrase** matches, not just individual words.

---

## **Common Mistakes to Avoid**

### **1. Not Using `GIN` Indexes**
If you skip the `GIN` index, FTS queries will force **sequential scans**, defeating the purpose.

❌ **Bad:**
```sql
SELECT * FROM products WHERE description_search @@ to_tsquery('english', 'running');
-- No index used!
```

✅ **Good:**
```sql
CREATE INDEX idx_products_search ON products USING GIN(description_search);
```

### **2. Forgetting to Update `tsvector` on Changes**
If you don’t use a **trigger** to update `tsvector` when `description` changes, your searches will be **stale**.

❌ **Manual Update (Error-Prone):**
```sql
UPDATE products SET description_search = to_tsvector('english', description);
-- Forgetting to run this after an UPDATE!
```

✅ **Use a Trigger (Recommended):**
```sql
CREATE TRIGGER update_product_search
BEFORE INSERT OR UPDATE OF description ON products
FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

### **3. Overusing `LIKE` for Search**
Even if `LIKE` works in small datasets, it **scales poorly**. Always prefer FTS for any meaningful search.

❌ **Anti-pattern:**
```sql
SELECT * FROM products WHERE description LIKE '%running%';
```

✅ **Use FTS instead:**
```sql
SELECT * FROM products WHERE description_search @@ to_tsquery('english', 'running');
```

### **4. Ignoring Stop Words**
PostgreSQL’s default `english` dictionary **filters out stop words** (`the`, `and`, `is`). If you want to include them, specify a different dictionary.

❌ **Missing Matches:**
```sql
-- "running shoes" won't match "the shoes for running" because "the" is filtered
```

✅ **Use `plain` Dictionary (No Stop Words):**
```sql
SELECT * FROM products
WHERE description_search @@ to_tsquery('plain', 'running & shoes');
```

### **5. Not Testing Edge Cases**
Always test:
- **Punctuation** (e.g., `"running,' shoes"` → should still match)
- **Case sensitivity** (`"Running"` vs `"running"`)
- **Accents** (`café` vs `cafe`)
- **Empty queries** (`SELECT * WHERE description_search @@ to_tsquery('english', '')`)

### **6. Forgetting to Vacuum Analyze**
FTS performance degrades over time as `tsvector` data grows. Run:

```sql
ANALYZE products;
VACUUM ANALYZE products;
```

---

## **Key Takeaways**

✅ **PostgreSQL FTS is powerful and lightweight**—no need for Elasticsearch if your search needs are simple.
✅ **`tsvector` + `GIN` index** = Fast, ranked searches.
✅ **Use `to_tsquery()` with `english` dictionary** for decent out-of-the-box results.
✅ **Leverage `ts_rank` for relevance-based sorting.**
✅ **Custom dictionaries** allow synonyms and stop-word control.
✅ **Always index `tsvector` columns** for performance.
✅ **Triggers keep `tsvector` in sync** with text changes.
❌ **Avoid `LIKE '%term%'`**—it’s slow and inflexible.
❌ **Don’t forget `ANALYZE`**—FTS degrades over time.
❌ **Test edge cases** (punctuation, case, accents).

---

## **When to Consider Elasticsearch**

While PostgreSQL FTS is **great for most applications**, Elasticsearch shines in these cases:
- **Millions of documents** (PostgreSQL FTS can struggle with **10M+ rows**).
- **Advanced analytics** (facets, aggregations, geospatial search).
- **Real-time indexing** (Elasticsearch syncs faster for high-velocity data).
- **Multi-language support** (better stemming/dictionaries).

For **80% of search use cases**, PostgreSQL FTS is **perfectly adequate**—and eliminates the complexity of managing another service.

---

## **Final Thoughts: Build It Yourself or Use the Right Tool?**

If you’re working with:
- A **medium-sized dataset** (<10M rows)
- **Simple to moderate search needs** (no faceting, no geospatial)
- **A PostgreSQL-heavy stack**

**Use PostgreSQL FTS—it’s powerful, free, and integrated.**

If you’re scaling to **millions of documents** or need **advanced features**, then Elasticsearch (or similar) makes sense.

---
**What’s your experience with PostgreSQL FTS? Have you optimized it for performance? Share your tips in the comments!**

🚀 **Happy searching!**
```