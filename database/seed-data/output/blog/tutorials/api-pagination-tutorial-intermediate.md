```markdown
---
title: "API Pagination Patterns: The Best (and Worst) Ways to Handle Large Result Sets"
description: "Learn the tradeoffs between offset, cursor, and keyset pagination, when to use each, and how to implement them correctly in your APIs."
author: "Alex Thompson"
date: "2023-10-15"
tags: ["API Design", "Database Patterns", "Performance", "Backend Engineering"]
---

# **API Pagination Patterns: The Best (and Worst) Ways to Handle Large Result Sets**

Pagination isn’t just a nicety—it’s a necessity. Returning thousands of records in a single API response is like serving a 20-course meal to someone who only has an appetite for appetizers. The result? Slow responses, crashed servers, and frustrated users who bail mid-request.

But how should you paginate? There are three dominant approaches—**offset-based**, **cursor-based**, and **keyset pagination**—each with strengths, weaknesses, and real-world tradeoffs. In this post, we’ll break down these patterns, show practical implementations, and discuss when to use each. By the end, you’ll know how to design paginated APIs that are performant, consistent, and user-friendly.

---

## **The Problem: Why Pagination Matters**

Imagine an e-commerce API returning all products for a user. A single query might return 100,000 records. If you blindly return the entire set:

1. **The database strains under the load** – A `SELECT *` with no filtering kills performance.
2. **The API times out** – Even with optimizations, large payloads exceed timeout limits.
3. **The client freezes** – Users wait for megabytes of JSON they’ll never scroll through.
4. **The server crashes** – Memory limits are exceeded, causing OOM errors.

Without pagination, APIs become unreliable at scale. That’s why almost every modern API—from Twitter to Stripe—uses pagination. The question isn’t *if* you should paginate, but **how**.

---

## **The Solution: Three Pagination Patterns**

We’ll explore three pagination strategies:

1. **Offset-Based Pagination** – The simplest approach, but often inefficient.
2. **Cursor-Based Pagination** – The most scalable, but requires special handling.
3. **Keyset Pagination** – A hybrid that borrows from both, optimized for ordered data.

Each has its own use cases, performance characteristics, and edge cases.

---

## **1. Offset-Based Pagination: The Crutch (But Sometimes the Right Tool)**

Offset-based pagination uses a skip-limit pattern:
- `OFFSET` tells the database to skip X rows.
- `LIMIT` restricts the result to Y rows.

### **Example: SQL Implementation**
```sql
-- Page 1 (offset=0, limit=10)
SELECT * FROM products LIMIT 10;

-- Page 2 (offset=10, limit=10)
SELECT * FROM products OFFSET 10 LIMIT 10;
```

### **Example: API Response**
```json
{
  "products": [
    { "id": 1, "name": "Laptop" },
    { "id": 2, "name": "Mouse" },
    ...
  ],
  "page": 2,
  "total_pages": 1000
}
```

### **Pros:**
- Simple to implement.
- Works with any database.

### **Cons:**
- **Terrible performance for large offsets** (e.g., `OFFSET 100000` forces a full scan).
- **Stale data risk**: If new records are inserted between requests, results may skip entries.
- **No consistency guarantees**: "Same page" might return different records if data changes.

### **When to Use:**
- Small datasets (under 1,000 records).
- Simple admin panels where performance isn’t critical.
- Legacy systems where rewriting isn’t an option.

---

## **2. Cursor-Based Pagination: The Scalable Choice**

Cursor-based pagination uses an opaque token (e.g., a UUID, timestamp, or auto-increment ID) to track position. Clients provide a cursor to fetch the next batch.

### **How It Works**
1. First request returns a cursor (e.g., `cursor="abc123"`).
2. Subsequent requests use this cursor for the `WHERE` clause.

### **Example: SQL Implementation**
```sql
-- First page (no cursor)
SELECT * FROM products ORDER BY id LIMIT 10;

-- Second page (using last seen id)
SELECT * FROM products WHERE id > ? ORDER BY id LIMIT 10;
```

### **Example: API Response**
```json
{
  "products": [
    { "id": 1, "name": "Laptop" },
    { "id": 2, "name": "Mouse" },
    ...
  ],
  "next_cursor": "eyJjYXRlIjoiMTIwNDAwMCIsImFkZCI6MX0=",
  "has_more": true
}
```

### **Pros:**
- **O(1) performance per page** (no large offsets).
- **No risk of stale data** (cursor is based on a single column).
- **Works well with distributed systems** (e.g., sharded databases).

### **Cons:**
- Requires an ordered column (e.g., `id`, `created_at`).
- More complex to implement than offset-based pagination.

### **When to Use:**
- Large datasets (millions of records).
- Real-time feeds (e.g., social media timelines).
- Microservices where consistency is critical.

---

## **3. Keyset Pagination: The Best of Both Worlds?**

Keyset pagination is similar to cursor-based but uses **range queries** (e.g., `WHERE id > last_seen_id`). It’s a middle ground between offset and cursor approaches.

### **Example: SQL Implementation**
```sql
-- First page (no previous ID)
SELECT * FROM products ORDER BY id LIMIT 10;

-- Next page (using last ID seen)
SELECT * FROM products WHERE id > ? ORDER BY id LIMIT 10;
```

### **Pros:**
- **No large database scans** (like offset-based).
- **Consistent results** (unlike offset-based).
- **Works with any ordered column** (not just auto-increment IDs).

### **Cons:**
- Requires an ordered column (e.g., `created_at`, `timestamp`).
- Slightly more complex than offset-based.

### **When to Use:**
- When you need consistency but don’t have a unique ID.
- For time-based data (e.g., "show me the last 100 orders").

---

## **Implementation Guide: Which One Should You Choose?**

| Pattern          | Best For                          | Performance | Consistency | Complexity |
|------------------|-----------------------------------|-------------|-------------|------------|
| **Offset-based** | Small datasets, quick hacks       | ❌ Poor      | ❌ Low       | ⭐ Low      |
| **Cursor-based** | High-scale APIs, real-time feeds | ✅ Excellent | ✅ High      | ⭐⭐ Medium |
| **Keyset**       | Ordered data, consistency needed  | ✅ Excellent | ✅ High      | ⭐⭐ Medium |

### **Recommendation:**
- **Default to cursor-based** if you have a unique ID column.
- **Use keyset** if you need consistency without a unique ID.
- **Avoid offset-based** unless you’re sure the dataset is small.

---

## **Common Mistakes to Avoid**

1. **Using `OFFSET` for large datasets** → Causes poor performance.
   - ❌ `SELECT * FROM users OFFSET 100000 LIMIT 10;` (terrible)
   - ✅ `SELECT * FROM users WHERE id > ? ORDER BY id LIMIT 10;` (better)

2. **Not handling missing cursors** → Clients might try to fetch beyond the last page.
   - Solution: Always include `has_more: false` when no next page exists.

3. **Relying on client-side sorting** → If clients sort differently, pagination breaks.
   - Solution: Always sort on the server.

4. **Ignoring edge cases** → What if the database changes between requests?
   - Solution: Use transactions or optimistic locking.

5. **Not returning metadata** → Users need to know if they’ve seen all results.
   - Solution: Always include `total_count`, `has_more`, and `next_cursor`.

---

## **Key Takeaways**

✅ **Cursor-based pagination is the gold standard** for scalability and consistency.
✅ **Keyset pagination is great for ordered data** (e.g., timestamps).
❌ **Offset-based pagination is usually the worst choice** for large datasets.
🔧 **Always test with real-world data**—local dev data often misrepresents production.
📊 **Include metadata** (`total_count`, `has_more`) to improve UX.
🔄 **Make cursors opaque** (e.g., encrypted UUIDs) to avoid exposing internal IDs.

---

## **Conclusion: Build APIs That Scale**

Pagination isn’t just about "making the API faster"—it’s about **building APIs that work at scale**. Whether you’re fetching user profiles, product listings, or real-time events, the right pagination strategy keeps your API responsive, reliable, and user-friendly.

- **For most cases, use cursor-based pagination** (it’s the most scalable).
- **For ordered data, keyset pagination is a strong alternative**.
- **Avoid offset-based pagination** unless you’re certain it won’t cause performance issues.

Now go forth and paginate wisely! 🚀

---
### **Further Reading**
- [Relay Cursor Connections (GraphQL)](https://relay.dev/graphql/connections.htm)
- [PostgreSQL Window Functions for Pagination](https://www.postgresql.org/docs/current/queries-lateral.html)
- [Cursor-Based Pagination in React (Next.js Example)](https://nextjs.org/docs/api-reference/next/router#router-is-fetching)
```

---
**Why this works:**
- **Code-first approach**: Each pattern includes SQL + API response examples.
- **Tradeoffs upfront**: The table makes decisions easy, but explanations back it up.
- **Practical advice**: Avoids theoretical jargon; focuses on real-world impact.
- **Actionable**: Ends with clear takeaways and "do this instead" guidance.