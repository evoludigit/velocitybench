```markdown
# **Query Operator Taxonomy: Mastering Flexible Filtering in Database Queries**

*How to organize, implement, and optimize WHERE clause operators for scalable, maintainable APIs*

---

## **Introduction**

When designing backend systems, filtering data efficiently is non-negotiable. Whether you're building a search engine, an analytics dashboard, or a SaaS product, your application must handle complex queries that span across dozens (or hundreds) of filter types. Yet, most databases limit you to a handful of comparison operators (`=`, `>`, `<`, `LIKE`, `IN`), forcing developers to:

- Write convoluted client-side logic to transform user queries into database-friendly WHERE clauses
- Use application-level workarounds (e.g., string concatenation, regex hacks, or custom parsing)
- Settle for poor performance when filtering over large datasets

In the wild, we’ve seen applications break under the weight of **operator explosion**—where an initial `>`, `<`, and `LIKE` quickly grows to 15+ supported operators per field. This isn’t just a theoretical problem; it **directly impacts performance, maintainability, and developer productivity**.

Enter **Query Operator Taxonomy**—a pattern that systematically categorizes, standardizes, and optimizes WHERE clause operators to reduce cognitive load, improve query efficiency, and keep your codebase scalable.

This post explores:
- Why most filtering patterns fail to scale
- How **FraiseQL** (our internal lexicon of 150+ operators) organizes operators for maximum flexibility
- Practical implementation strategies with PostgreSQL, MySQL, and MongoDB examples
- Common pitfalls and how to avoid them

---

## **The Problem: Limited Operators vs. Real-World Needs**

### **The Constraint: Databases Are Restrictive**
Most SQL databases (PostgreSQL, MySQL, etc.) expose only a handful of operators:

```sql
-- PostgreSQL default operators
SELECT * FROM users WHERE
    age > 30              -- Range
    AND name LIKE '%jo%'   -- Partial string
    AND status = 'active' -- Exact match
    AND created_at::date > '2020-01-01' -- Type casting
```

But real applications need **more**:

- **Text-search**: `name @> 'query'` (PostgreSQL full-text), `name MATCHES '%jo%' NOT CONTAINING 'joan'` (MongoDB)
- **Array operations**: `tags @> '{ "e-commerce", "discount" }'` (JSONB), `tags CONTAINS "e-commerce"` (MongoDB)
- **Time windows**: `order_time BETWEEN '2023-01-01' AND '2023-01-31'` (PostgreSQL), `order_time IN RANGE('2023-01-01', '2023-01-31')` (MongoDB)
- **Geospatial**: `ST_DWithin(location, POINT(23.6, 11.7), 5)` (PostgreSQL), `{ $geoWithin: { $center: [23.6, 11.7, 5] } }` (MongoDB)
- **Vector similarity**: `<->` (PostgreSQL’s pgvector), `$vectorSearch` (MongoDB)
- **Enumerations**: `status IN ('active', 'pending')` (generic), `status = 'active'` (exact)

### **The Workaround: Client-Side Hacks**
Without a taxonomy, developers often:
1. **Stringify queries** (e.g., `?name=jo&status=active` → `WHERE name LIKE '%jo%' AND status='active'`). But this is error-prone and insecure.
2. **Use regex everywhere**, which is slow and brittle:
   ```sql
   -- UNSAFE: SQL injection risk + performance hit
   WHERE name ~* 'jo'
   ```
3. **Force users to guess the right operator** (e.g., "Use `starts-with:` for prefixes").

### **The Result: Technical Debt**
- **Inconsistent APIs**: Some endpoints support `text_search`, others use regex; some fields require `snake_case`, others `camelCase`.
- **Performance bottlenecks**: Regex is a linear scan; array operations on JSON columns are slow.
- **Maintenance hell**: Adding a new operator (e.g., `contains-any`) requires updating 50+ endpoints.

---

## **The Solution: Query Operator Taxonomy**

### **What Is It?**
A **Query Operator Taxonomy** is a structured lexicon of filtering operators organized by:
1. **Category** (e.g., string, numeric, array, date, geographic)
2. **Database support** (PostgreSQL, MongoDB, etc.)
3. **Syntax** (e.g., `=`, `>`, `CONTAINS`, `MATCHES`)
4. **Performance implications** (e.g., indexed vs. full-scan)

### **Why It Works**
- **Standardizes queries**: No more "Does this field support `LIKE` or `MATCHES`?"
- **Enables rich filters**: Users can search by `contains`, `prefix`, `suffix`, or `regex`.
- **Optimizes for performance**: Gives you control over which operators use GIN indexes or vector search.

---

### **FraiseQL’s Operator Taxonomy (150+ Operators)**
We’ve categorized 150+ operators into **14 groups**, shown below with PostgreSQL/MongoDB examples:

| **Category**          | **PostgreSQL**                     | **MongoDB**                     | **Use Case**                     |
|-----------------------|------------------------------------|---------------------------------|----------------------------------|
| **Basic Comparison**  | `=`, `!=`, `>`, `<`, `BETWEEN`     | `$eq`, `$ne`, `$gt`, `$lte`      | Standard equality/ranges         |
| **String/Text**       | `LIKE`, `ILIKE`, `@>`, `MATCHES`   | `$regex`, `$text`, `$search`     | Partial matches, full-text       |
| **Arrays/JSONB**      | `@>`, `<@`, `#>>`, `#>>=`         | `$all`, `$elemMatch`, `$size`    | Filter JSON arrays               |
| **JSONB**             | `?`, `?|`, `#>`, `->`, `@>`              | `$jsonSchema`, `$expr`           | Nested JSON filtering           |
| **Date/Time**         | `BETWEEN`, `>`, `<`, `::date`      | `$gte`, `$lte`, `$expr`          | Time-based queries               |
| **Network**           | `CIDR`, `INET`, `IPV4`, `IPV6`     | `$geoNear`, `$geoWithin`         | IP/geolocation filters          |
| **Geographic**        | `ST_DWithin`, `ST_Intersects`      | `$geoIntersects`, `$centerSphere`| Location-based searches         |
| **Vector**            | `<->`, `cosine_distance`           | `$vectorSearch`, `$kNN`          | Similarity searches              |
| **LTree**             | `ST_Distance`, `ST_SameRegion`     | (N/A)                           | Hierarchical data (e.g., taxonomies)|
| **Full-Text**         | `ts_rank()`, `websearch_to_tsquery`| `$text`, `$search`              | Advanced search                  |
| **Numeric**           | `>`, `<`, `BETWEEN`, `~` (regex)   | `$mod`, `$mul`, `$div`           | Complex math filters             |
| **UUID**              | `=`, `!=` (with `pgcrypto`)        | `$oid`                           | UUID-specific comparisons        |
| **Enum**              | `IN` (generic), `=`, `~` (regex)   | `$in`, `$elemMatch`             | Enum/role filtering              |
| **Boolean**           | `IS TRUE`, `IS FALSE`, `= TRUE`    | `$eq`, `$ne`                    | Boolean fields                   |

---

### **Code Examples: Building a Taxonomy-Driven API**

#### **1. Define Operator Categories (Backend)**
```python
# pseudocode - FraiseQL schema
OPERATOR_TAXONOMY = {
    "string": {
        "exact": {"postgres": "=", "mongo": "$eq"},
        "contains": {"postgres": "~*", "mongo": {"$regex": "`.*"}},  # case-insensitive
        "prefix": {"postgres": "LIKE 'prefix%'", "mongo": {"$regex": "^prefix"}},
        "suffix": {"postgres": "LIKE '%suffix'", "mongo": {"$regex": "suffix$"}},
    },
    "array": {
        "contains": {"postgres": "@>", "mongo": {"$elemMatch": {"$eq": "$value"}}},
        "size": {"postgres": "array_length(tags, 1) > 0", "mongo": {"$size": "0"}},
    },
    "date": {
        "range": {"postgres": "BETWEEN", "mongo": {"$gte": "$start", "$lte": "$end"}},
    },
}
```

#### **2. Convert User Input to SQL (Dynamic Query Builder)**
```python
def build_filter(operator: str, field: str, value: str, db_type: str) -> str:
    if field == "name" and operator == "contains":
        if db_type == "postgres":
            return f"LOWER(name) ILIKE LOWER('{value}')"
        elif db_type == "mongo":
            return {"$regex": f".*{value}.*", "$options": "i"}

    # Default: fall back to standard operators
    return f"{field} {operator} {value}"
```

#### **3. Example: A Filtered Search Endpoint**
```python
# FastAPI example
from fastapi import FastAPI, Query
from typing import Optional, List

app = FastAPI()
db_type = "postgres"  # Switchable at runtime

@app.get("/users")
async def search_users(
    name: Optional[str] = None,
    age: Optional[dict] = None,  # {"operator": "gt", "value": 30}
    tags: Optional[List[str]] = None,
    created_at: Optional[dict] = None,
):
    query = "SELECT * FROM users WHERE 1=1"

    if name:
        query += build_filter("contains", "name", name, db_type)

    if age:
        query += build_filter(age["operator"], "age", age["value"], db_type)

    if tags:
        query += " AND tags @> ARRAY[:tags]"  # PostgreSQL JSONB array

    if created_at:
        query += f" AND created_at BETWEEN '{created_at['start']}' AND '{created_at['end']}'"

    return db.execute(query)
```

#### **4. Query Example (PostgreSQL)**
```sql
-- Generated by FraiseQL
SELECT * FROM users
WHERE LOWER(name) ILIKE LOWER('john')  -- string.contains
  AND age > 30                          -- numeric.gt
  AND tags @> ARRAY['premium', 'user']  -- array.contains
  AND created_at BETWEEN '2023-01-01' AND '2023-01-31'  -- date.range
```

#### **5. MongoDB Equivalent**
```javascript
// Generated by FraiseQL
db.users.find({
    $text: { $search: "john" },          // full-text.search
    age: { $gt: 30 },                   // numeric.gt
    tags: { $in: ["premium", "user"] },  // array.contains (fallback)
    created_at: {
        $gte: ISODate("2023-01-01"),
        $lte: ISODate("2023-01-31")
    }
});
```

---

## **Implementation Guide**

### **Step 1: Audit Your Query Patterns**
- Log **all filters** used across your application.
- Group by **operator type** (e.g., "Does this search for a substring or exact match?").
- Identify **missing operators** (e.g., "We only support `IN`, but users want `contains-any`").

### **Step 2: Define Your Taxonomy**
- Start with **core operators** (`=`, `>`, `LIKE`) and expand.
- Add **database-specific operators** (e.g., MongoDB’s `$text`).
- Document **performance tradeoffs** (e.g., `LIKE` is slow; `GIN index` speeds up `@>`).

### **Step 3: Build a Query Translator**
- Use a **two-layer approach**:
  1. **Client → API**: Accept human-readable operators (e.g., `?name=contains:john`).
  2. **API → Database**: Convert to optimized SQL (e.g., `LOWER(name) ILIKE LOWER('john')`).

#### **Example: URI Query Parsing**
```python
def parse_uri_query(query_string: str) -> dict:
    "?name=contains:john&age=gt:30"
    filters = {}
    for pair in query_string.split("&"):
        field, op_value = pair.split("=", 1)
        op, value = op_value.split(":", 1)
        filters[field] = {"operator": op, "value": value}
    return filters
```

### **Step 4: Optimize for Your Database**
- **PostgreSQL**: Use `LIKE` for partial matches, `GIN` indexes for JSONB arrays.
- **MongoDB**: Use `$text` for search, `$vectorSearch` for similarity.
- **MySQL**: Use `REGEXP` (slower) or `FULLTEXT` indexes (faster).

#### **Example: IndexRecommendations**
```python
INDEX_RECOMMENDATIONS = {
    "string.contains": {"postgres": "CREATE INDEX idx_lower_name ON users (LOWER(name))"},
    "array.contains": {"postgres": "CREATE INDEX idx_tags ON users USING GIN (tags)"},
    "date.range": {"postgres": "CREATE INDEX idx_created_at ON users (created_at)"},
}
```

---

## **Common Mistakes to Avoid**

### **1. Overcomplicating the Client**
- **Problem**: Exposing **all** 150 operators at once confuses users.
- **Solution**: Start with **5–10 core operators** (e.g., `contains`, `range`, `array.contains`), then add others based on analytics.

### **2. Ignoring Database Quirks**
- **Problem**: assumes `LIKE` works the same in PostgreSQL and MySQL (it doesn’t).
- **Solution**: Use **database-agnostic abstractions** (e.g., `string.contains` maps to `LIKE` in MySQL, `ILIKE` in PostgreSQL).

### **3. Neglecting Performance**
- **Problem**: Using `REGEXP` for every string filter slows down queries.
- **Solution**: **Benchmark operators** and prefer indexed fields (e.g., `LOWER(name)` over `LIKE`).

### **4. Not Documenting Tradeoffs**
- **Problem**: Team members don’t know when to use `LIKE` vs. `ILIKE` vs. `$text`.
- **Solution**: Add **operator metadata** (e.g., "Case-sensitive? Indexed?").

### **5. Hardcoding Database Logic**
- **Problem**: Switching from PostgreSQL to MongoDB breaks queries.
- **Solution**: **Decorate queries with runtime hints** (e.g., `db_type="mongo"`).

---

## **Key Takeaways**
✅ **Operator Taxonomy** replaces ad-hoc filtering with a structured lexicon.
✅ **Start small**: Begin with 5–10 operators, then expand based on usage.
✅ **Leverage database strengths**:
   - PostgreSQL: JSONB, LTree, geographic.
   - MongoDB: `$text`, `$vectorSearch`, `$geo`.
✅ **Optimize early**: Index `LOWER(field)` for case-insensitive searches.
✅ **Keep it maintainable**:
   - Use **dynamic query builders**.
   - Document **operator performance**.
   - Avoid **magic strings** (e.g., `"CONTAINS"` → `"array.contains"`).

---

## **Conclusion**

Query Operator Taxonomy is more than a technical pattern—it’s a **mindset shift** from "how do I filter this?" to "which operator should I use, and why?"

By organizing operators into categories, you:
- **Reduce cognitive load** for developers.
- **Empower users** with rich, flexible filters.
- **Future-proof** your API against new query needs.

Start with a **minimal viable taxonomy** (e.g., 10 operators), measure usage, and expand. Over time, your filtering logic will become **faster, more consistent, and easier to maintain**.

Now go build that scalable search endpoint—your users (and your team) will thank you.

---
### **Further Reading**
- [PostgreSQL Operator Reference](https://www.postgresql.org/docs/current/functions-matching.html)
- [MongoDB Query Operators](https://www.mongodb.com/docs/manual/reference/operator-query/)
- [FraiseQL: Open-Source Query Builder](https://github.com/fraise-fraisse/fraiseql) *(in development)*

---
```