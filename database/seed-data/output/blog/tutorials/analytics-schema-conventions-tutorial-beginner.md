```markdown
# **Analytics Schema Conventions & Best Practices: Build Data Warehouses That Scale & Feel Intuitive**

![Analytics Schema Pattern](https://via.placeholder.com/1200x400?text=Analytics+Schema+Pattern+Illustration)

As backend developers, we often build systems where data lives in databases, APIs serve it, and analysts query it for insights. But what happens when your analytics schema becomes a tangled mess—mixing raw transactions with pre-aggregated summaries, using inconsistent column types, or leaving critical indexes undefined?

This makes querying painful, performance unpredictable, and new developers lost. **That’s where analytics schema conventions come in.** They bring order to chaos by defining how tables, columns, and indexes *should* be structured—so your codebase feels like a well-organized document, not a jumbled notebook.

In this post, we’ll explore a **real-world pattern** used by systems like FraiseQL. We’ll cover table naming, column types, indexing strategies, and why these rules unlock cleaner code, better performance, and even automated compiler introspection.

---

## **Why Analytics Schemas Need Conventions**
Imagine you’re working on a project where developers add tables and columns without a strategy. Over time, you might end up with:

- A `sales` table mixing raw transactions (`price`, `currency`) with pre-aggregates (`total_revenue`).
- A `users` table where some demographic fields are stored as SQL columns (`age`, `country`), while others are nested in JSON (`metadata`).
- No clear index strategy, so queries on `user_id` or `date` are slow.

This chaos leads to:
❌ **Hard-to-maintain code** – New engineers waste time figuring out table structures.
❌ **Poor performance** – Inconsistent indexing causes unpredictable query speeds.
❌ **Compiler limitations** – Tools like FraiseQL can’t auto-optimize if schemas lack structure.

**Conventions fix this.** They act like **contracts**—every developer agrees to follow the same rules, making the system predictable and performant.

---

## **The Problem: Why Most Analytics Schemas Fail**
Without clear conventions, analytics schemas suffer from several pain points:

### **1. Compiler Can’t Distinguish Fact vs. Aggregate Tables**
A fact table (`tf_sales`) stores raw events (e.g., individual transactions), while an aggregate table (`ta_daily_sales`) stores precomputed metrics (e.g., daily revenue).

But if your schema has:
```sql
-- A messy mix of raw and aggregated data
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product VARCHAR(100),
    revenue NUMERIC,
    daily_total NUMERIC  -- This is an aggregate, but looks like raw data!
);
```
...how does a query optimizer or a tool like FraiseQL know which columns are safe to aggregate?

### **2. Measures and Dimensions Are Inconsistent**
**Measures** are numeric columns (e.g., `sum(revenue)`).
**Dimensions** are attributes used for filtering/groupping (e.g., `customer_id`, `product_category`).

If you store dimensions in both SQL columns and JSON (e.g., `metadata->>'address'`), querying becomes messy:
```sql
-- Which path should I use for filtering?
SELECT sum(revenue)
FROM sales
WHERE customer_id = 123
   OR metadata->>'country' = 'USA';  -- Inconsistent!
```

### **3. No Clear Indexing Strategy**
Without rules, indexes are either:
- **Over-indexed** (wasting storage, slow writes).
- **Under-indexed** (slow queries).

Example:
```sql
-- No index on `date`, so full table scans!
SELECT sum(revenue) FROM sales WHERE date BETWEEN '2023-01-01' AND '2023-01-31';
```

### **4. Hard to Navigate**
A schema like this:
```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id INT,
    action VARCHAR(50),
    details JSONB  -- Where are the dates stored?!
);
```
...forces developers to constantly check documentation, slowing down development.

---

## **The Solution: FraiseQL’s Analytics Schema Conventions**
FraiseQL enforces **three core rules** to make analytics schemas **self-documenting, performant, and tool-friendly**:

| **Component**          | **Rule**                                                                 | **Why It Matters**                                                                 |
|------------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Table Naming**       | `tf_*` = Fact tables (`raw events`), `ta_*` = Aggregates (`precomputed`) | Compilers know which tables to optimize for aggregations.                     |
| **Column Types**       | Measures in SQL, dimensions in JSONB (or indexed SQL types)              | Separates numeric data (for math) from categorization (for filtering).          |
| **Indexing**           | GIN for JSONB, B-tree for filters, BRIN for time-series                 | Ensures fast lookups without over-indexing.                                       |
| **JSONB Structure**    | Flat paths, consistent naming (`dimensions.user_id` instead of `user`)    | Makes querying predictable.                                                       |

Let’s dive into each rule with examples.

---

## **Implementation Guide: Practical Examples**

### **1. Table Naming: `tf_*` for Facts, `ta_*` for Aggregates**
**Fact Tables (`tf_*`)**
Store raw, unaggregated events. Example: `tf_user_events`.

```sql
CREATE TABLE tf_user_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB  -- Contains dimensions like `device`, `country`
);
```

**Aggregate Tables (`ta_*`)**
Store precomputed metrics. Example: `ta_daily_user_metrics`.

```sql
CREATE TABLE ta_daily_user_metrics (
    date DATE PRIMARY KEY,
    user_count INT NOT NULL,
    revenue NUMERIC(10,2) NOT NULL,
    active_users INT NOT NULL
);
```
**Why?**
- Fact tables are ingested first (slow writes, fast reads).
- Aggregate tables are refreshed periodically (faster writes, cached reads).
- Tools like FraiseQL can auto-generate aggregations from `tf_*` tables.

---

### **2. Column Types: Measures in SQL, Dimensions in JSONB**
**Measures (SQL Columns)**
Numeric values used for aggregations (`SUM`, `AVG`).

```sql
CREATE TABLE tf_sales (
    id BIGSERIAL PRIMARY KEY,
    revenue NUMERIC(10,2),  -- Measure: Can be summed
    quantity INT            -- Measure: Can be counted
);
```

**Dimensions (JSONB or Indexed SQL)**
Attributes for filtering/groupping (e.g., `customer_id`, `product_category`).

```sql
CREATE TABLE tf_sales (
    -- ... other measures ...
    dimensions JSONB NOT NULL DEFAULT '{}'  -- Contains:
    -- {
    --   "customer_id": 123,
    --   "product_category": "electronics",
    --   "country": "USA"
    -- }
);
```
**Key Tradeoffs:**
✅ **Pros:**
- JSONB allows flexible schemas (e.g., adding new dimensions without migrations).
- Measures in SQL are optimized for math operations.

❌ **Cons:**
- JSONB requires **GIN indexes** for querying (see next section).
- Overusing JSONB can make queries slower than indexed SQL columns.

**Example Query:**
```sql
-- Filter by SQL index (fast)
SELECT sum(revenue)
FROM tf_sales
WHERE customer_id = 123;

-- Filter by JSONB (requires GIN index)
SELECT sum(revenue)
FROM tf_sales
WHERE dimensions->>'country' = 'USA';
```

---

### **3. Indexing Strategy: GIN, B-tree, and BRIN**
| **Data Type**       | **Index Type** | **When to Use**                          | **Example**                          |
|---------------------|----------------|------------------------------------------|--------------------------------------|
| `JSONB`             | `GIN`          | For filtering on nested JSON fields      | `CREATE INDEX idx_geolocation ON tf_events USING GIN (dimensions);` |
| `INT`, `VARCHAR`    | `B-tree`       | Default for equality/range queries       | `CREATE INDEX idx_user_id ON tf_events (user_id);` |
| `TIMESTAMPTZ`       | `BRIN`         | Time-series data (PostgreSQL)            | `CREATE INDEX idx_time ON tf_events USING BRIN (timestamp);` |

**Example Schema with Indexes:**
```sql
CREATE TABLE tf_user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    dimensions JSONB NOT NULL DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_user_id ON tf_user_sessions (user_id);
CREATE INDEX idx_time ON tf_user_sessions USING BRIN (start_time);
CREATE INDEX idx_location ON tf_user_sessions USING GIN (dimensions);
```

**Why This Works:**
- **GIN indexes** handle JSONB efficiently (e.g., `WHERE dimensions->>'country' = 'USA'`).
- **BRIN indexes** are lightweight for time-series (PostgreSQL).
- **B-tree** is the default for simple equality/range queries.

---

### **4. JSONB Path Conventions: Flat and Consistent**
To avoid query ambiguity, follow these rules for JSONB paths:
1. **Use dot notation** (`dimensions.user_id` instead of `metadata.user`).
2. **Keep paths flat** (avoid `user -> profile -> name`; use `user_profile_name`).
3. **Document paths** in a `README` or schema tool.

**Good:**
```sql
-- Consistent path: user.id
SELECT sum(revenue)
FROM tf_sales
WHERE dimensions->>'user.id' = 123;
```

**Bad (ambiguous):**
```sql
-- Which path is correct? user.id or user->id?
SELECT sum(revenue)
FROM tf_sales
WHERE dimensions?'user.id';  -- Risky!
```

---

## **Common Mistakes to Avoid**
| **Mistake**                          | **Example**                                      | **Fix**                                                                 |
|--------------------------------------|--------------------------------------------------|--------------------------------------------------------------------------|
| Mixing fact and aggregate tables     | `sales` table has both raw and pre-aggregated data | Split into `tf_sales` (raw) and `ta_daily_sales` (precomputed).         |
| Overusing JSONB for measures         | Storing `revenue` in JSONB instead of SQL        | Measures should be SQL columns (`NUMERIC`, `INT`).                        |
| No indexes on filtered columns      | Querying `WHERE dimensions->>'country'` without a GIN index | Always index dimensions used for filtering.                            |
| Inconsistent JSONB paths             | `user.id` vs. `user->id`                         | Stick to one path convention (e.g., dot notation).                     |
| Ignoring BRIN for time-series        | Full scans on `timestamp` columns                | Use `BRIN` for large time-series tables.                                 |

---

## **Key Takeaways**
Here’s what you should remember:

✅ **Table Naming:**
- `tf_*` = Fact tables (raw events).
- `ta_*` = Aggregates (precomputed metrics).

✅ **Column Types:**
- **Measures** (numbers) → SQL columns (`NUMERIC`, `INT`).
- **Dimensions** (categories) → JSONB or indexed SQL columns.

✅ **Indexing:**
- `GIN` for JSONB filtering.
- `B-tree` for default SQL columns.
- `BRIN` for time-series data.

✅ **JSONB Structure:**
- Use **flat paths** (`dimensions.user_id`).
- **Document paths** clearly.

✅ **Compiler Benefits:**
- Tools like FraiseQL can **auto-optimize** queries if conventions are followed.
- New developers **instantly understand** the schema.

---

## **Conclusion: Build Analytics Systems That Scale**
Analytics schemas don’t have to be a messy dumping ground. By adopting **consistent conventions**, you:
1. **Improve performance** with targeted indexing.
2. **Reduce bugs** by separating measures and dimensions.
3. **Enable tooling** like FraiseQL to auto-optimize.

**Start small:**
- Audite your current schema. Are tables mixed (`sales` = raw + aggregates)?
- Add `tf_`/`ta_` prefixes to new tables.
- Index dimensions and time-series columns.

Over time, your analytics layer will feel **intentional, fast, and maintainable**—just like the well-organized spreadsheet it is.

---
**Further Reading:**
- [PostgreSQL GIN Indexes](https://www.postgresql.org/docs/current/indexes-gist.html)
- [BRIN Indexes for Time-Series](https://www.postgresql.org/docs/current/btree-brin.html)
- [FraiseQL’s Approach to Analytics](https://fraiseql.com/docs)

**Got questions?** Reply below—I’d love to hear how you’re structuring your analytics schemas!
```

---
### **Why This Works for Beginners**
1. **Code-first approach**: SQL examples show *exactly* how to apply rules.
2. **Analogies**: Compares schema conventions to file systems (folders for `tf_`/`ta_`, columns for measures/dimensions).
3. **Tradeoffs**: Honest about JSONB flexibility vs. indexing tradeoffs.
4. **Actionable mistakes**: Lists common pitfalls with fixes.