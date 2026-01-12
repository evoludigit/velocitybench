```markdown
# **Composite WHERE Operators: Building Flexible Filters for Real-World Queries**

*How to design database queries that scale from simple to complex—without breaking performance or your sanity.*

---

## **Introduction**

Ever spent hours writing a SQL query that feels more like a puzzle than a database operation? You start with a simple `WHERE` clause—say, filtering users by email—and suddenly realize you need to:
- Combine multiple conditions *and/or*
- Exclude certain records *not*
- Nest conditions within conditions *arbitrarily deep*

This is the **composite WHERE operators problem**: creating flexible, reusable filters that handle real-world complexity while maintaining performance.

In this post, we’ll explore:
✅ How to design **composite filters** (AND/OR/NOT combinations)
✅ A practical API pattern to compose them safely
✅ Tradeoffs between flexibility and query complexity

No more hardcoded `WHERE` clauses that break when requirements change.

---

## **The Problem: When Simple Filters Aren’t Enough**

Imagine building an e-commerce search system. A user might want:
- *Product is in stock AND price < $50 AND category = "Books"*
- *OR*
- *Product was released in 2023 AND has at least 4.5 stars*

Here’s how a naive implementation might look:

```sql
-- ❌ Hardcoded mix of AND/OR with magic strings
SELECT * FROM products
WHERE (category = 'Books' AND price < 50 AND stock > 0)
   OR (release_year = 2023 AND rating >= 4.5);
```

**Problems:**
1. **Hard to maintain**: Logic is scattered across queries.
2. **Performance fragility**: Adding a new condition requires rewriting the entire query.
3. **No reuse**: Complex filter logic can’t be shared across apps or services.

For larger systems, this quickly becomes unmanageable. You need a structured way to combine filters dynamically.

---

## **The Solution: Composite WHERE Operators**

The **Composite WHERE Operators** pattern lets you:
✔ **Combine filters** using logical operators (`AND`, `OR`, `NOT`)
✔ **Nest conditions** arbitrarily deep
✔ **Track query complexity** to enforce performance limits

### **Core Idea**
Instead of writing queries manually, we define a **filter builder** that:
1. Represents each condition as a small, reusable object
2. Composes them using operator methods (`&&`, `||`, `!`)
3. Translates the structure into SQL (or another dialect)

### **Example: A Filter Builder in Code**

Here’s a TypeScript-like pseudocode for a composite filter system:

```typescript
// Base Filter Interface
interface Filter {
  match(data: Record<string, any>): boolean;
  toSQL(columns: string[]): string;
}

// AND/NOT Operators
const and = (a: Filter, b: Filter): Filter => ({
  match(data) { return a.match(data) && b.match(data); },
  toSQL(columns) { return `( ${a.toSQL(columns)} AND ${b.toSQL(columns)} )` }
});

const not = (filter: Filter): Filter => ({
  match(data) { return !filter.match(data); },
  toSQL(columns) { return `( NOT ${filter.toSQL(columns)} )` }
});

// Example: Build a complex filter
const isBookAndCheap =
  and(
    eq('category', 'Books'),
    lt('price', 50),
    gt('stock', 0)
  );

const isPopularNewRelease =
  and(
    eq('release_year', 2023),
    gte('rating', 4.5)
  );

const finalFilter = or(isBookAndCheap, isPopularNewRelease);

// Translate to SQL
const sql = finalFilter.toSQL([
  'category', 'price', 'stock', 'release_year', 'rating'
]);
// Output:
// SELECT ... WHERE
//   ((category = 'Books' AND price < 50 AND stock > 0)
//    OR (release_year = 2023 AND rating >= 4.5))
```

---

## **Implementation Guide: FraiseQL Style**

For a database query builder like **FraiseQL**, we’d design it with these components:

### **1. Operator Classes**
Define reusable filter types:

```typescript
class EqualityFilter extends Filter {
  constructor(private column: string, private value: any) {}
  match(row) { return row[this.column] === this.value; }
  toSQL() { return `${this.column} = ?`; }
}

class GreaterThanFilter extends Filter {
  constructor(private column: string, private value: any) {}
  match(row) { return row[this.column] > this.value; }
  toSQL() { return `${this.column} > ?`; }
}
```

### **2. Composite Operators**
Combine filters using `AND`, `OR`, `NOT`:

```typescript
class AndComposite extends Filter {
  constructor(private filters: Filter[]) {}
  match(row) { return this.filters.every(f => f.match(row)); }
  toSQL() {
    return this.filters.map(f => f.toSQL()).join(' AND ');
  }
}

class OrComposite extends Filter {
  constructor(private filters: Filter[]) {}
  match(row) { return this.filters.some(f => f.match(row)); }
  toSQL() {
    return this.filters.map(f => f.toSQL()).join(' OR ');
  }
}
```

### **3. Query Builder API**
Expose a fluent interface:

```typescript
const builder = new QueryBuilder();
const filters = builder
  .where('price').lt(50)
  .and('category').eq('Books')
  .or()
  .where('release_year').eq(2023)
  .and('rating').gte(4.5);

// Build SQL and params
const { sql, params } = builder.build();
/*
SQL: SELECT ... WHERE (price < ? AND category = ? OR release_year = ? AND rating >= ?)
Params: [50, 'Books', 2023, 4.5]
*/
```

### **4. Query Complexity Enforcement**
To prevent slow queries, track operator depth:

```typescript
class QueryBuilder {
  private depth = 0;
  private maxDepth = 3; // Reject queries with >3 nested operators

  // ...
  or() {
    if (this.depth >= this.maxDepth) throw new Error('Query too complex');
    this.depth++;
    return this;
  }
  // ...
}
```

---

## **Common Mistakes to Avoid**

1. **Nesting too deep**: Complexity explodes with every layer. Stick to 2–3 levels unless absolutely necessary.
   ```sql
   -- ⚠️ "Y combinator" anti-pattern
   WHERE (col1 = 'a' AND (col2 = 'b' OR (NESTED_SQL_HERE))) ...
   ```

2. **Overusing `OR`**: `OR` queries often force full-table scans. Prefer `AND` where possible.
   ```sql
   -- ❌ Inefficient
   WHERE (col1 = 'a' OR col2 = 'b') AND col3 > 0

   -- ✅ Better
   WHERE (col1 = 'a' AND col3 > 0) OR (col2 = 'b' AND col3 > 0)
   ```

3. **Ignoring database hints**: Some databases optimize composite queries differently. Test thoroughly.

4. **Tight coupling**: Don’t expose raw `toSQL()`—abstract the translation layer for future changes.

---

## **Key Takeaways**

- **Problem**: Manual `WHERE` clauses become unmaintainable as requirements grow.
- **Solution**: Use a **filter builder** to compose conditions with `AND`, `OR`, `NOT`.
- **Tradeoffs**:
  - *Flexibility*: Allows deep nesting but risks performance.
  - *Reusability*: Filters can be shared across queries but may expose model details.
- **Best practices**:
  - Enforce query depth limits.
  - Defer SQL generation until the end.
  - Profile frequently to catch regressions.

---

## **Conclusion**

Composite WHERE operators give you the power to craft complex filters safely—without sacrificing readability or performance. By structuring them as composable objects (like FraiseQL), you get:
✅ Clean, maintainable logic
✅ Reusable components
✅ Controls for query complexity

**Next steps**:
- Experiment with your own filter builder.
- Benchmark against raw SQL for critical queries.
- Consider database-specific optimizations (e.g., covering indexes).

Need inspiration? Check out [FraiseQL’s documentation](https://fraise.dev) for a full example of this pattern in action.

---

*Have questions? Drop them in the comments or tweet at me—I’m happy to help!* 🚀
```