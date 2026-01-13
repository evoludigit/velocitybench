```markdown
# **"Batteries Not Included": The Extension Requirements Pattern for Scalable Backends**

*How to gracefully depend on PostgreSQL extensions without locking yourself into monolithic architecture*

---

## **Introduction**

Imagine your team built a **search-heavy** SaaS platform using PostgreSQL. After months of development, user queries scale perfectly—until they don’t. Suddenly, you realize your existing `LIKE` queries can’t handle faceted search, and your team is torn between:

- **Option 1:** Rewrite all queries to use a separate search engine (Elasticsearch).
- **Option 2:** Drop `LIKE` and rebuild indexing from scratch.
- **Option 3:** *Avoid the problem entirely* by designing for extensibility from the start.

This third option is where the **Extension Requirements** pattern comes in.

PostgreSQL’s ecosystem thrives on extensions like `pgvector` (vector search), `postgis` (geo-spatial), `pg_trgm` (fuzzy string matching), and `hstore` (JSON-like). These tools solve niche problems brilliantly—but **hard-coupling them into your schema locks you into maintenance hell**. The Extension Requirements pattern lets you **delay implementation decisions**, **swap components**, and even **migrate incrementally** without refactoring entire application layers.

In this guide, we’ll explore:
✅ **Why extensions cause pain** (and how to avoid it)
✅ **How to model database features as pluggable components**
✅ **Practical code examples** for feature flags and dynamic behavior
✅ **Common pitfalls** (and how to debug them)

---

## **The Problem: "It Works on My Machine"**

Extensions are powerful—but they’re **opinionated**. A single extension can dictate:

```sql
CREATE EXTENSION IF NOT EXISTS pgvector;
-- Now you're forced to use $1.<<>.$2 syntax for similarity queries.
```

This exposes your application to hidden dependencies:
1. **Schema Lock-in:** Your search queries depend on `pgvector`’s `vector` type.
2. **Version Risks:** Downgrading PostgreSQL means dropping extensions.
3. **Feature Bloat:** Consumers might not need `postgis`, but your schema assumes they do.

### **Real-World Example: The Faceted Search Dilemma**

Let’s say your analytics dashboard needs **multi-field filtering**. Without careful design, you might end up with:

```sql
-- ❌ Hard-coupled to pgvector
SELECT * FROM products
WHERE vector_column <<> $1::vector
AND price BETWEEN $2 AND $3;
```

This query **cannot run** without `pgvector` installed. If you later decide to use **Meilisearch** instead, you’ll need to rewrite **every API endpoint** that touches this table.

---

## **The Solution: Extension Requirements Pattern**

The **Extension Requirements** pattern treats database features as **runtime capabilities** rather than hard constraints. Here’s how it works:

1. **Schema Agnosticism:** Design tables/queries to work *without* specific extensions.
2. **Feature Flags:** Make database logic conditional on extension availability.
3. **Polyfill Support:** Provide fallback behavior if an extension isn’t installed.

### **Core Principles**
| Principle | Example |
|-----------|---------|
| **Assume Nothing** | Avoid types like `vector`; use plain columns (`float[]` instead). |
| **Separate Logic** | Query logic lives in stored procedures, not application code. |
| **Fallback Gracefully** | If `pg_trgm` is missing, use `LEVENSHTAIN()` instead of `SIMILARITY()`. |

---

## **Components & Solutions**

### **1. Modular Schema Design**
Instead of:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    -- ❌ Coupled to pgvector
    embeddings vector(3)  -- What if we later switch to Meilisearch?
);
```

Use:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    -- ✅ Agnostic: Store as plain array
    embedding float[]  -- Can be converted to/from pgvector
);
```

### **2. Dynamic Query Execution**
Store search logic in **stored procedures** and route calls based on available extensions:

```sql
CREATE FUNCTION get_products_with_search(
    query_search_text TEXT,
    query_embedding float[]
) RETURNS SETOF products AS $$
DECLARE
    has_pgvector BOOLEAN;
BEGIN
    -- Check if pgvector is available
    SELECT EXISTS (
        SELECT 1 FROM pg_available_extensions
        WHERE name = 'pgvector'
    ) INTO has_pgvector;

    IF has_pgvector THEN
        -- Use vector search (requires pgvector)
        RETURN QUERY EXECUTE format('
            SELECT * FROM products
            WHERE embedding =%L %I::vector
            ORDER BY embedding <-> %L::vector
            LIMIT 10
        ', query_embedding);
    ELSE
        -- Fallback: Use simple text search
        RETURN QUERY EXECUTE format('
            SELECT * FROM products
            WHERE to_tsvector(%L, name || ' ' || description)
            @@to_tsquery(%L)
            LIMIT 10
        ', 'english', query_search_text);
    END IF;
END;
$$ LANGUAGE plpgsql;
```

### **3. Feature Flags in Application Code**
This pattern requires application-layer awareness. In Node.js (using `pg`), you might do:

```javascript
const { Client } = require('pg');

async function getProducts(client, searchQuery) {
    const res = await client.query(`
        SELECT
            extension_available('pgvector') AS has_pgvector,
            (SELECT name FROM pg_available_extensions WHERE name = 'pgvector') AS pgvector_ext
    `);

    const hasPgvector = res.rows[0].has_pgvector;

    if (hasPgvector) {
        // Use vector search
        return await client.query(`
            SELECT * FROM products
            WHERE embedding = %L %I::vector
            ORDER BY embedding <-> %L::vector
            LIMIT 10
        `, [searchQuery.vector, searchQuery.vector]);
    } else {
        // Fallback to text search
        return await client.query(`
            SELECT * FROM products
            WHERE to_tsvector('english', name || ' ' || description)
            @@to_tsquery($1)
            LIMIT 10
        `, [searchQuery.text]);
    }
}
```

### **4. Migrations Without Downtime**
Use **feature flags** to enable extensions in stages:

```sql
-- Migration Step 1: Add columns but no logic
ALTER TABLE products ADD COLUMN embedding float[];

-- Migration Step 2 (later): Enable pgvector
CREATE EXTENSION pgvector;
UPDATE products SET embedding = vector_transform(/* convert existing data */);
```

---

## **Implementation Guide**

### **Step 1: Audit Your Current Schema**
Walk through your database and ask:
- Which extensions are **assumed** (e.g., `postgis` for `ST_Distance`)?
- Which queries **can’t run without them**?

Example tooling:
```sql
-- Find all functions using pgvector
SELECT routine_name, routine_schema
FROM information_schema.routines
WHERE routine_definition LIKE '%vector%';
```

### **Step 2: Replace Direct Dependencies**
| Dependency | Agnostic Alternative |
|------------|----------------------|
| `vector` type | `float[]` + manual conversion |
| `ST_GeomFromText` | `WKB` or `GeoJSON` strings |
| `pg_trgm` similarity | Custom `LEVENSHTAIN()` logic |

### **Step 3: Build a Capability Registry**
Create a helper function to check for extensions:

```sql
CREATE OR REPLACE FUNCTION extension_available(ext_name TEXT) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_extension
        WHERE extname = ext_name
    );
END;
$$ LANGUAGE plpgsql;
```

### **Step 4: Route Logic Dynamically**
Modify your APIs to **inspect capabilities** and route accordingly.

---

## **Common Mistakes to Avoid**

### **🚫 Mistake 1: Hardcoding Extension Logic in App Code**
❌ *Bad* (database dependency leaks into app):
```javascript
// Application code depends on pgvector!
if (searchMethod === 'vector') {
    // BAD: Tight coupling!
    return client.query(`
        SELECT * FROM products WHERE embedding <<> $1
    `, [searchQuery]);
}
```

✅ *Good* (delegation to database):
```javascript
// Application code delegates to database capabilities
return client.query(`
    SELECT get_products_with_search(%L, %L)
`, [searchText, searchEmbedding]);
```

### **🚫 Mistake 2: Forgetting to Test Without Extensions**
Always test fallback behavior:
```sql
-- Test your fallback logic
SELECT get_products_with_search('test', ARRAY[]::float[])
-- Should NOT crash if pgvector is missing!
```

### **🚫 Mistake 3: Overcomplicating Polyfills**
Avoid "reinventing the wheel" for simple cases. For `pg_trgm`, it’s often fine to use:
```sql
-- Fallback to native Postgres similarity
SELECT name FROM products
WHERE similarity(name, 'query') > 0.7
```

---

## **Key Takeaways**

✅ **Schema Agnosticism:** Design tables to work without extensions.
✅ **Dynamic Routing:** Use stored procedures to route logic based on available extensions.
✅ **Fallbacks:** Always provide graceful degradation (e.g., text search without vector).
✅ **Feature Flags:** Enable extensions incrementally to reduce risk.
✅ **Test Edge Cases:** Verify behavior when extensions are absent.

---

## **Conclusion**

The **Extension Requirements** pattern is a **lifeline** for teams that need to:
- **Avoid vendor lock-in** (PostgreSQL extensions are powerful but brittle).
- **Scale incrementally** (add features without a full rewrite).
- **Support diverse environments** (not all customers have `pgvector` installed).

By treating database extensions as **optional capabilities**, you build systems that remain **flexible, maintainable, and adaptable**—even as requirements evolve.

### **Next Steps**
1. **Audit your current schema** for hidden extension dependencies.
2. **Start small**: Refactor one feature (e.g., search) using this pattern.
3. **Document your polyfills**: Keep a live list of fallback behaviors.

Would you like a follow-up post on **migrating from `pgvector` to Meilisearch** using this approach? Let me know in the comments!

---
*Note: All code examples use PostgreSQL 15. Ensure your environment supports `vector` and `pg_trgm` features if needed.*
```