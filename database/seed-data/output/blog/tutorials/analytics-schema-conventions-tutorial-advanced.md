```markdown
# Analytics Schema Design for Backends: A Pattern Language

*How FraiseQL’s Strict Conventions Enable Compiler Magic and Scalable Performance*

---

## Introduction: The Analytics Schema Dilemma

Analytics systems are the DNA of modern data-driven products. They power everything from user behavior dashboards to revenue forecasting, and their performance has a direct impact on business decisions. But designing an analytics schema isn’t just about storing numbers—it’s about balancing flexibility, query efficiency, and long-term maintainability.

Most backend engineers I’ve worked with approach analytics schemas with a blank slate, mixing tables, column types, and indexing strategies haphazardly. The result? A fragile system where:
- Developers waste time guessing which table is the "right" one for analysis
- Queries become painfully slow as new dimensions are added
- Performance degrades predictably as data scales
- Debugging analytics queries turns into a game of "Where’s Waldo?"

This volatility isn’t inevitable. FraiseQL, the query compiler that powers our analytics layer, uses strict conventions to turn analytics schemas into reliable, high-performance assets. In this post, we’ll explore the **"Analytics Schema Conventions"** pattern—the bedrock of FraiseQL’s design. You’ll learn how intentional naming, column typing, and indexing strategies enable compiler introspection and consistent performance at scale.

---

## The Problem: Conventionless Analytics Schemas

Let’s start with a familiar scenario. Imagine a SaaS platform tracking user engagement with a schema that evolved organically:

```sql
-- Table created in 2019, slightly modified over time
create table user_activity (
    activity_id uuid primary key,
    user_id text not null,
    event_type text not null,
    created_at timestamp with time zone not null,
    -- "Dimensions" added as columns over time
    page_url text,
    referrer text,
    device_type text,
    -- "Aggregates" computed and stored here
    session_length integer,
    scroll_depth numeric,
    -- JSONB added later for complexity
    metadata jsonb,
    -- More ad-hoc columns...
    ip_address inet
);

-- A new table for "facts"
create table page_views (
    view_id serial primary key,
    user_id text not null,
    page_id text not null,
    referrer text,
    visit_time timestamp with time zone not null,
    -- Measures mixed with dimensions
    duration_ms bigint,
    bounce boolean,
    -- JSONB "dimensions"
    user_properties jsonb,
    -- No clear indexing strategy
    created_at timestamp with time zone
);
```

### The Consequences of No Schema Conventions

1. **Compiler Confusion**: Without conventions, tools like FraiseQL can’t distinguish between:
   - "Fact tables" (high-cardinality, measure-heavy tables)
   - "Aggregate tables" (pre-computed summaries)
   - "Flat tables" (simple, row-by-row records)

2. **Ambiguous Semantics**:
   - Is `duration_ms` a measure? A dimension? A derived column?
   - Does `jsonb` contain dimensions, or arbitrary metadata?
   - Which columns should be *indexed*—and how?

3. **Performance Pitfalls**:
   - JSONB *can* be indexed, but it’s often overlooked
   - Time-series data *should* be BRIN-indexed, but who knows?
   - Dimensional data *should* be B-tree indexed, but it’s easy to forget

4. **Developer Fatigue**:
   - New engineers guess which table to query
   - Adding a new dimension requires manual schema updates
   - Queries become brittle as conventions shift

---

## The Solution: FraiseQL’s Analytics Schema Pattern

FraiseQL’s pattern is a **system of conventions** that transforms analytics schemas from a fragile black box into a high-performance, self-documenting asset. The core components are:

1. **Table Naming Prefixes**: Explicitly classify tables by purpose
2. **Column Type Rules**: Strictly separate measures, dimensions, and metadata
3. **Index Strategy**: Predefined indexing rules for performance
4. **JSONB Path Conventions**: Structure nested data predictably

These conventions enable compiler introspection—FraiseQL can *analyze* the schema, auto-suggest optimizations, and even rewrite queries for better performance.

---

## Implementation Guide: Code Examples

Let’s build a schema using FraiseQL’s conventions for an e-commerce platform tracking product views and purchases.

### 1. Table Naming Prefixes

FraiseQL uses two prefixes to distinguish table types:
- `tf_*` → **Fact tables** (high-cardinality, measure-driven)
- `ta_*` → **Aggregate tables** (pre-computed summaries)

#### Example: Fact Table (`tf_product_views`)
```sql
create table tf_product_views (
    id bigserial primary key,
    user_id uuid not null,
    product_id uuid not null,
    session_id uuid not null,
    -- Measures (numeric, indexed)
    view_count integer not null,
    avg_duration_ms bigint not null,
    -- "Filter columns" (B-tree indexed)
    view_time timestamp with time zone not null,
    -- Dimensions (JSONB)
    user_properties jsonb not null,
    -- Flat dimensions (B-tree indexed)
    device_type varchar(32),
    country_code varchar(2)
);
```

#### Example: Aggregate Table (`ta_daily_metrics`)
```sql
create table ta_daily_metrics (
    date timestamp with time zone primary key,
    product_id uuid not null,
    -- Measures
    total_views integer not null,
    revenue numeric not null,
    -- Flat dimensions (B-tree indexed)
    category varchar(64)
);
```

### 2. Column Type Rules

FraiseQL enforces three categories for columns:

#### A. Measures (Numeric, Analytical)
- Stored as columns, *not* in JSONB
- Examples: `view_count`, `avg_duration_ms`, `revenue`
- **Indexing**: GIN (for array measures) or B-tree (for scalar measures)

```sql
-- Measures are numeric, indexed
alter table tf_product_views add constraint check_measures positive(
    view_count,
    avg_duration_ms
);
create index idx_tf_product_views_measure_components on tf_product_views using gin (
    -- Array measures (if applicable)
    array_agg_measure_1,
    array_agg_measure_2
);
```

#### B. Dimensions (JSONB)
- All non-measure, non-filter data goes in JSONB
- **Convention**: Use dot notation for nested fields (e.g., `user_properties.first_name`)

```json
-- Valid JSONB dimension format
{
  "user_properties": {
    "first_name": "Alice",
    "age": 28,
    "premium_member": true
  },
  "referral_source": "facebook",
  "traffic_channel": "social"
}
```

#### C. Filter Columns (B-tree Indexed)
- Columns used for filtering (e.g., `user_id`, `product_id`, `view_time`)
- **Rule**: Always index these with B-tree

```sql
-- Filter columns are B-tree indexed by default
create index idx_tf_product_views_user_id on tf_product_views (user_id);
create index idx_tf_product_views_product_id on tf_product_views (product_id);
```

### 3. Index Strategy

FraiseQL’s indexing rules for analytics tables:

| **Data Type**       | **Index Type** | **When to Use**                          | **Example**                          |
|---------------------|-----------------|-------------------------------------------|---------------------------------------|
| JSONB               | GIN             | For nested dimensions (e.g., `user_properties`) | `create index idx_tf_json_gin on tf_product_views using gin (user_properties jsonb_path_ops);` |
| Time-series         | BRIN            | For timestamp columns (`view_time`)       | `create index idx_brin_view_time on tf_product_views using brin (view_time);` |
| Filter columns      | B-tree           | For `user_id`, `product_id`, etc.         | `create index idx_user_id on tf_product_views (user_id);` |

#### Example: BRIN for Time-Series
```sql
-- BRIN for high-cardinality time-series data
create index idx_brin_product_views_time on tf_product_views
    using brin (view_time)
    with (brin_block_thresh := 1000);
```

#### Example: GIN for JSONB
```sql
-- GIN for JSONB dimensions
create index idx_json_user_properties on tf_product_views
    using gin (user_properties jsonb_path_ops);
```

### 4. JSONB Path Conventions

To ensure consistency, FraiseQL enforces:
- **Flat paths**: Avoid deep nesting (e.g., `a.b.c` instead of `a.b.c.d`)
- **Reserved prefixes**:
  - `user_*` → User attributes (e.g., `user_id`, `user_properties`)
  - `event_*` → Event metadata (e.g., `event_timestamp`, `event_source`)
- **Type hints**: Include type info in paths (e.g., `user_properties.boolean_flag`)

#### Example: Consistent JSONB Structure
```json
-- Good: Flat paths, type hints
{
  "user_properties": {
    "first_name": "string",
    "is_premium": true,
    "age": 28
  },
  "event_metadata": {
    "source": "web",
    "device": "mobile"
  }
}
```

---

## Implementation Guide: Putting It All Together

### Step 1: Design Your Fact Tables
1. Start with `tf_<entity>` (e.g., `tf_user_sessions`, `tf_order_items`).
2. Separate measures (numeric) from dimensions (JSONB).
3. Index filter columns with B-tree.

```sql
create table tf_order_items (
    id bigserial primary key,
    order_id uuid not null,
    user_id uuid not null,
    product_id uuid not null,
    -- Measures
    quantity integer not null,
    unit_price numeric not null,
    -- Filter columns
    order_date timestamp with time zone not null,
    -- Dimensions
    user_properties jsonb not null,
    product_properties jsonb not null
);

-- Indexes
create index idx_tf_order_items_order_id on tf_order_items (order_id);
create index idx_tf_order_items_product_id on tf_order_items (product_id);
create index idx_tf_order_items_brin_time on tf_order_items using brin (order_date);
create index idx_json_user_properties on tf_order_items using gin (user_properties jsonb_path_ops);
```

### Step 2: Design Aggregate Tables
1. Use `ta_<entity>` (e.g., `ta_daily_sales`).
2. Pre-compute measures (e.g., `total_revenue`, `item_count`).
3. Include flat dimensions for filtering.

```sql
create table ta_daily_sales (
    date timestamp with time zone primary key,
    category varchar(64) not null,
    -- Measures
    total_revenue numeric not null,
    order_count integer not null,
    unique_users integer not null
);

-- Index for filtering by category
create index idx_ta_daily_sales_category on ta_daily_sales (category);
```

### Step 3: Add FraiseQL Compiler Support
FraiseQL’s compiler can now:
- Infer table types (fact/aggregate) from prefixes
- Auto-suggest measures vs. dimensions
- Generate optimal indexes for queries

```sql
-- FraiseQL query example
-- Compiler auto-detects:
-- - tf_order_items as a fact table
-- - Measures: quantity, unit_price
-- - Filter: order_date >= '2023-01-01'
SELECT
    user_id,
    SUM(quantity) as total_items,
    SUM(unit_price * quantity) as revenue
FROM tf_order_items
WHERE order_date >= '2023-01-01'
GROUP BY user_id;
```

---

## Common Mistakes to Avoid

1. **Mixing Measures and Dimensions in JSONB**
   - *Bad*: Storing `revenue` in JSONB because "it’s just a number."
   - *Why*: JSONB adds overhead for numeric values; use columns for measures.

2. **Over-Indexing JSONB**
   - *Bad*: Creating GIN indexes on every JSONB column.
   - *Why*: GIN indexes have overhead; only index dimensions used in queries.

3. **Ignoring BRIN for Time-Series**
   - *Bad*: Using B-tree for timestamp columns in high-cardinality tables.
   - *Why*: BRIN is optimized for time-series data.

4. **Deeply Nested JSONB**
   - *Bad*: `user.address.city` instead of `user.city`.
   - *Why*: Flatter paths improve query performance.

5. **Skipping Filter Column Indexes**
   - *Bad*: Forgetting to index `user_id` or `product_id`.
   - *Why*: These are *always* used for filtering.

6. **Ad-Hoc Table Naming**
   - *Bad*: `analytics_events`, `user_behavior`, `stats`.
   - *Why*: Prefixes (`tf_`, `ta_`) enable compiler logic.

---

## Key Takeaways

✅ **Conventions Enable Compiler Magic**
- FraiseQL’s compiler relies on strict naming (`tf_`, `ta_`) to optimize queries.

✅ **Separate Measures, Dimensions, and Metadata**
- Measures → SQL columns (numeric, indexed)
- Dimensions → JSONB (flat paths, type hints)
- Filters → B-tree indexed columns

✅ **Index Strategically**
- **GIN** for JSONB dimensions
- **BRIN** for time-series data
- **B-tree** for filter columns

✅ **Flat is Fast**
- JSONB paths should be shallow (e.g., `user.city` > `user.address.city`).

✅ **Performance Scales with Conventions**
- Consistent schemas reduce query variability and improve cache hits.

---

## Conclusion: Build for the Compiler, Not the Query

Analytics schemas aren’t just storage—they’re the foundation for high-performance queries. By adopting FraiseQL’s conventions, you’re not just documenting your schema; you’re *enabling* compiler optimizations that would otherwise be impossible.

The pattern isn’t about rigid rules—it’s about **intentional design**. When your schema communicates clearly (via naming, typing, and indexing), the compiler can do its job: turning raw data into actionable insights with minimal effort.

### Next Steps
1. **Audit your analytics schema**: Map out your tables, measures, and dimensions. Do they follow conventions?
2. **Refactor incrementally**: Start with one fact table and enforce `tf_<entity>`.
3. **Experiment with indexes**: Try BRIN for time-series, GIN for JSONB.
4. **Adopt a compiler**: Tools like FraiseQL make conventions worthwhile.

Analytics isn’t just about the data—it’s about the *system* that serves it. Start building that system today.

---
**Further Reading**
- [FraiseQL Documentation](https://fraise.com/docs)
- [PostgreSQL BRIN Indexes](https://www.postgresql.org/docs/current/rules-brin.html)
- [Practical PostgreSQL Indexing](https://use-the-index-luke.com/)

---
*What’s your analytics schema like today? Share your challenges in the comments—let’s discuss!*
```