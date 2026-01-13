# **Analytics Schema Conventions & Best Practices: Build Scalable, Queryable Data Warehouses**

*(With Real-World Examples in PostgreSQL)*

---

## **Introduction**

Data analytics is about more than just writing queries—it’s about designing schemas that **scale under load**, **optimize performance**, and **reduce developer friction**. Without clear conventions, even well-structured analytics systems can become a tangled mess of tables with inconsistent naming, poorly indexed columns, and dimensions buried in JSON.

In this post, we’ll explore **FraiseQL’s schema design patterns**—a battle-tested approach for structuring analytics tables that enables:
✅ **Compiler introspection** (for tools like FraiseQL)
✅ **Consistent query performance**
✅ **Cleaner codebases** (easier navigation & refactoring)
✅ **Future-proofing** against growing analytics needs

We’ll dive into **PostgreSQL** examples, but these principles apply to any relational database.

---

## **The Problem: When Analytics Schemas Go Haywire**

Imagine maintaining an analytics system with tables like this:

```sql
-- Table 1: Sales data mixed with aggregations
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product_name TEXT,
    revenue NUMERIC,
    region JSONB,
    "2023-01" NUMERIC,  -- Monthly revenue (hardcoded)
    "2023-02" NUMERIC,
    -- ...
    "user_actions" JSONB
);

-- Table 2: Raw user events (No clear separation)
CREATE TABLE user_events (
    event_id BIGSERIAL PRIMARY KEY,
    user_id INT,
    event_type TEXT,
    metadata JSONB,
    timestamp TIMESTAMPTZ NOT NULL
);

-- Table 3: Aggregates scattered everywhere
CREATE TABLE aggregate_sales (
    date DATE,
    revenue NUMERIC,
    products_count INT
);
```

### **What Goes Wrong?**
1. **Compiler Can’t Understand the Schema**
   - No clear distinction between **fact tables** (raw data) and **aggregate tables** (precomputed metrics).
   - Tools like FraiseQL **struggle to generate efficient queries** because they don’t know what’s a measure vs. a dimension.

2. **Dimensions Get Lost in JSON**
   - `region` could be a filterable dimension, but it’s buried in `JSONB` with no indexing strategy.
   - `metadata` might contain useful filters (`"event_type"`, `"device_type"`), but search performance is terrible.

3. **Indexes Are Guesswork**
   - Should `user_id` (filterable) be indexed? What about `event_type` (dimension)?
   - Without conventions, developers waste time tuning indexes manually.

4. **Time-Series Data Is Unoptimized**
   - Monthly revenue columns (`"2023-01"`, `"2023-02"`) force **dense indexing**, hurting performance at scale.
   - No **BRIN indexes** for time-series efficiency.

5. **Codebase Becomes Inconsistent**
   - New developers (or you, 6 months from now) have to **reverse-engineer** which columns are important.
   - Refactoring becomes risky—what if you rename a dimension but break queries?

### **The Cost of Chaos**
- **Slower queries** (missing indexes, poor JSONB search)
- **Harder debugging** (unpredictable performance)
- **Technical debt** (scattered aggregations, no clear patterns)

---

## **The Solution: FraiseQL’s Analytics Schema Conventions**

FraiseQL (and similar systems) enforces **strict naming and structural rules** to solve these problems. The key idea:
> **Consistency enables tooling to optimize queries automatically.**

Here’s how it works:

| **Component**               | **Convention**                          | **Why It Matters** |
|-----------------------------|----------------------------------------|--------------------|
| **Table Naming**            | `tf_*`: Fact tables, `ta_*`: Aggregate tables | Clear separation for compiler logic |
| **Measures**                | SQL columns (`NUMERIC`, `INT`, etc.)   | Fast filtering & aggregation |
| **Dimensions**              | JSONB with flat paths                   | Flexible schema, indexed via GIN |
| **Filter Columns**          | Indexed SQL types (`INT`, `DATE`, etc.) | Predictable performance |
| **Time-Series**             | BRIN indexes                           | Scales for historical data |
| **JSONB Structure**         | Consistent nesting (e.g., `{"dimension": "value"}`) | Reliable querying |

---

## **Implementation Guide: Building a Proper Analytics Schema**

Let’s refactor our messy example into a **FraiseQL-compatible** schema.

### **1. Fact Tables (`tf_*`) – Raw Data with Clear Measures & Dimensions**

```sql
-- Fact table for sales (tf_sales)
CREATE TABLE tf_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    order_id UUID NOT NULL,       -- Filter column (indexed)
    product_id INT NOT NULL,      -- Filter column (indexed)
    revenue NUMERIC NOT NULL,     -- Measure (SQL column)
    region JSONB NOT NULL,        -- Dimension (indexed via GIN)
    user_id INT NOT NULL,         -- Filter column (indexed)
    timestamp TIMESTAMPTZ NOT NULL -- Time-series (BRIN-indexed)
);

-- GIN index for JSONB dimensions (region, user_metadata)
CREATE INDEX idx_tf_sales_region ON tf_sales USING GIN (region);

-- B-tree index for filterable columns
CREATE INDEX idx_tf_sales_order_id ON tf_sales (order_id);
CREATE INDEX idx_tf_sales_product_id ON tf_sales (product_id);
CREATE INDEX idx_tf_sales_user_id ON tf_sales (user_id);

-- BRIN index for time-series ( PostgreSQL 10+ )
CREATE INDEX idx_tf_sales_timestamp_brin ON tf_sales USING BRIN (timestamp);
```

**Key Takeaways:**
- **Measures (`revenue`)** are **SQL columns** (fast for aggregations).
- **Dimensions (`region`)** live in **JSONB** but are **indexed with GIN**.
- **Filters (`order_id`, `product_id`)** get **B-tree indexes**.
- **Time-series (`timestamp`)** uses **BRIN** for efficiency.

---

### **2. Aggregate Tables (`ta_*`) – Precomputed Metrics**

```sql
-- Aggregate table for daily revenue (ta_daily_revenue)
CREATE TABLE ta_daily_revenue (
    date DATE PRIMARY KEY,
    total_revenue NUMERIC NOT NULL,  -- Measure
    product_count INT NOT NULL,       -- Measure
    top_3_regions JSONB NOT NULL     -- Dimension (e.g., {"regions": ["NA", "EU", "APAC"]})
);

-- GIN index for JSONB dimensions
CREATE INDEX idx_ta_daily_revenue_top_regions ON ta_daily_revenue USING GIN (top_3_regions);
```

**Why This Works:**
- **Precomputed aggregations** avoid expensive joins.
- **Dimensions (`top_3_regions`)** are still flexible but indexed.
- **Primary key (`date`)** ensures fast lookups.

---

### **3. JSONB Best Practices (Flat & Predictable Structure)**

FraiseQL expects **flat, consistent JSONB paths**. Bad:

```json
{"user": {"id": 123, "preferences": {"theme": "dark"}}}
```

Good (FraiseQL-style):

```json
{"user_id": 123, "theme": "dark"}
```

**Example: Indexing User Metadata**

```sql
-- Fact table with user metadata
CREATE TABLE tf_user_events (
    event_id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    event_type TEXT NOT NULL,  -- Filter column (indexed)
    metadata JSONB NOT NULL,   -- {"device": "mobile", "browser": "chrome", ...}
    timestamp TIMESTAMPTZ NOT NULL
);

-- GIN index for all JSONB dimensions
CREATE INDEX idx_tf_user_events_metadata ON tf_user_events USING GIN (metadata);

-- B-tree index for filterable columns
CREATE INDEX idx_tf_user_events_event_type ON tf_user_events (event_type);
```

**Query Example (FraiseQL-style):**
```sql
-- Get mobile users in EU (compiler understands dimensions)
SELECT COUNT(*)
FROM tf_user_events
WHERE metadata->>'device' = 'mobile'
  AND region->>'continent' = 'EU';
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Mixing Measures & Dimensions in JSONB**
**Problem:**
```sql
CREATE TABLE bad_sales (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL  -- {"revenue": 100, "region": "NA", ...}
);
```
**Why Bad:**
- **No clear separation** between metrics (`revenue`) and attributes (`region`).
- **Compiler can’t optimize** (e.g., FraiseQL won’t know `revenue` is a measure).

**Fix:**
```sql
CREATE TABLE good_sales (
    sale_id BIGSERIAL PRIMARY KEY,
    revenue NUMERIC NOT NULL,  -- Measure (SQL)
    region TEXT NOT NULL,      -- Dimension (indexed)
    metadata JSONB             -- {"device": "mobile", ...}
);
```

---

### **❌ Mistake 2: Over-Indexing JSONB**
**Problem:**
```sql
-- Indexing every possible JSONB path is slow
CREATE INDEX idx_slow_json ON tf_sales (metadata);
CREATE INDEX idx_slow_json2 ON tf_sales (metadata->>'device');
```
**Why Bad:**
- **Too many indexes** hurt write performance.
- **FraiseQL may ignore** partial paths if the schema is unclear.

**Fix:**
- **Index only what’s needed** (e.g., `metadata->>'device'` if frequently filtered).
- **Use partial indexes** for large tables.

---

### **❌ Mistake 3: Using Dense Time-Series Indexes**
**Problem:**
```sql
-- Monthly revenue in columns (inefficient for analytics)
CREATE TABLE bad_time_series (
    month DATE PRIMARY KEY,
    jan_revenue NUMERIC,
    feb_revenue NUMERIC,
    -- ... 12 columns!
);
```
**Why Bad:**
- **Updates are slow** (updating 12 columns per month).
- **Hard to query** (e.g., "show me revenue for May 2023").

**Fix:**
```sql
-- Time-series optimized for BRIN
CREATE TABLE good_time_series (
    date DATE PRIMARY KEY,
    revenue NUMERIC NOT NULL
);

-- BRIN index for fast range scans
CREATE INDEX idx_brin_revenue ON good_time_series USING BRIN (date);
```

---

### **❌ Mistake 4: Ignoring Compiler Expectations**
**Problem:**
FraiseQL expects:
- `tf_*` for facts.
- `ta_*` for aggregates.
- Measures in SQL columns.

If you name tables arbitrarily (e.g., `analytics.sales_data`), **the compiler won’t optimize queries** as well.

**Fix:**
Stick to the naming convention:
```sql
-- ✅ Good
CREATE TABLE tf_sales ( ... );

-- ❌ Bad (confuses tools)
CREATE TABLE analytics.sales ( ... );
```

---

## **Key Takeaways: The FraiseQL Analytics Schema Playbook**

| **Best Practice**               | **Implementation**                          | **Why It Matters** |
|----------------------------------|--------------------------------------------|--------------------|
| **Use `tf_*` for facts**        | `tf_user_events`, `tf_sales`                | Compiler knows it’s raw data |
| **Use `ta_*` for aggregates**   | `ta_daily_revenue`, `ta_weekly_metrics`    | Precomputed for speed |
| **Measures in SQL columns**     | `revenue NUMERIC`, `count INT`             | Fast aggregations |
| **Dimensions in JSONB**         | `{"region": "EU", "device": "mobile"}`      | Flexible schema |
| **GIN indexes for JSONB**       | `CREATE INDEX ON tf_events USING GIN (metadata)` | Efficient JSON searches |
| **B-tree for filterable columns** | `CREATE INDEX ON tf_sales (product_id)`    | Predictable performance |
| **BRIN for time-series**        | `CREATE INDEX ON tf_events USING BRIN (timestamp)` | Scales for history |
| **Flat JSONB structure**        | `{"user_id": 123, "theme": "dark"}`         | Reliable querying |
| **Consistent naming**           | Avoid `analytics.sales`, use `tf_sales`     | Tools can optimize |

---

## **Conclusion: Build for Scale from Day One**

FraiseQL’s schema conventions aren’t just a "nice-to-have"—they’re a **must** for:
✅ **Fast, predictable query performance**
✅ **Easier maintenance** (no more guessing schema intent)
✅ **Compiler-driven optimizations** (FraiseQL, Presto, etc.)
✅ **Future-proofing** (adding new dimensions won’t break queries)

### **Next Steps**
1. **Audit your analytics schema** – Does it follow these conventions?
2. **Start small** – Refactor one `tf_*` and one `ta_*` table as a proof of concept.
3. **Use FraiseQL (or similar tools)** to see the compiler’s optimizations in action.
4. **Document your conventions** – Keep the team on the same page.

**Final Thought:**
> *"A well-structured analytics schema isn’t about perfect tables—it’s about reducing friction so you can focus on insights, not infrastructure."*

---
**What’s your analytics schema like? Are you using similar conventions? Share your experiences in the comments!** 🚀