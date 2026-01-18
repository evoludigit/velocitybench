```markdown
---
title: "SQL Query Composition: Building High-Performance APIs with FraiseQL"
date: "February 10, 2024"
author: "Alex Carter"
tags: ["database", "API design", "query optimization", "SQL", "GraphQL"]
---

# SQL Query Composition: Building High-Performance APIs with FraiseQL

*Tired of slow APIs that feel like they're dragging a sledgehammer through a thimble? Learn how SQL Query Composition—specifically through patterns like FraiseQL—can transform your data fetching from a performance nightmare into a high-octane experience. This isn't just another "how databases work" lecture; it's a battle plan for fixing real-world backend bottlenecks.*

---

## Introduction

Building APIs is like cooking a meal: you can either chop vegetables one by one (N+1 queries) or prepare everything at once (efficiently joined SQL). Most backend engineers start with "good enough" approaches—directly translating ORM queries to SQL or naively joining related tables—only to realize later that their APIs aren't scaling under load. Enter **SQL Query Composition**, a pattern where complex queries are intelligently assembled into single optimized SQL statements. This isn't about reinventing SQL; it’s about *smartly combining* it to match the needs of your application’s data consumers.

The industry has seen this problem before. Early on, ORMs like Django ORM or ActiveRecord abstracted away SQL entirely, leading to N+1 query problems where a single "fetch users" endpoint could execute hundreds of individual queries. Developers then shifted to manual JOINs—only to realize that ORMs were too limited and manual SQL was too error-prone. Now, APIs like GraphQL introduce even more complexity: clients can request nested data structures, and the server must compose queries efficiently.

In this post, we'll explore **SQL Query Composition**, a pattern that bridges these gaps. We’ll focus on **FraiseQL**, a framework that intelligently composes nested queries into single optimized SQL statements using JOIN strategies, CTEs, and subqueries. By the end, you’ll understand why this works, how it outperforms alternatives, and how to implement it in your own projects.

---

## The Problem: Naive SQL Generation Leads to Inefficiency

If you’ve ever worked on a backend system that suddenly slows to a crawl after adding a few new feature requests, you’re likely dealing with one of two problems:
1. **N+1 Query Problem**: Fetching a list of items where each item triggers a separate query for related data (e.g., fetching a list of blog posts, each with a separate query for comments).
2. **Inefficient JOINs**: Writing JOIN-heavy SQL that the database optimizer struggles to handle, leading to excessive memory usage or timeouts.

Let’s illustrate both with code examples.

### Example 1: The N+1 Query Problem

Imagine a simple API endpoint that returns a list of blog posts with their authors. Here’s a naive implementation using Django ORM:

```python
# Naive implementation (N+1 queries!)
posts = BlogPost.objects.all()
for post in posts:
    author = Author.objects.get(id=post.author_id)
    print(f"Post {post.title} by {author.name}")
```

This might look harmless, but under the hood, it triggers:
- **1 query** to fetch all `BlogPost` objects.
- **N queries** (where N is the number of posts) to fetch each `Author`.

If you have 100 posts, that’s 101 queries. Scale this to 1,000 posts, and you’re now making 1,001 queries—each one a potential latency hit.

### Example 2: Inefficient JOINs

What if you *do* write a JOIN, but don’t consider the database optimizer’s perspective? Here’s a JOIN that might seem correct but could be optimized better:

```sql
-- Inefficient JOIN (columns multiplied)
SELECT p.title, a.name, c.content
FROM posts p
JOIN authors a ON p.author_id = a.id
JOIN comments c ON p.id = c.post_id;
```

This query joins three tables, but if the `comments` table is large, you might end up with a Cartesian product-like explosion where every `posts` row is combined with every `comments` row. The optimizer might not catch this if the query is malformed.

### The Cost of Inefficiency
- **Performance**: More queries = higher latency.
- **Scalability**: Systems slow down as data grows.
- **Debugging**: Harder to trace which queries are slow.
- **Resource usage**: Databases waste CPU and memory on inefficient operations.

---

## The Solution: SQL Query Composition with FraiseQL

FraiseQL (pronounced "fraise") is a pattern and framework for composing **nested** SQL queries into a single optimized query. It’s inspired by GraphQL’s query composition but optimized for SQL’s strengths. The key idea is to:
1. **Analyze the requested data structure** (e.g., "posts with authors").
2. **Intelligently JOIN tables** based on what’s needed.
3. **Use CTEs (Common Table Expressions) and subqueries** to break down complex logic.
4. **Leverage the database optimizer** to handle the heavy lifting.

FraiseQL achieves this by:
- **Static analysis** of the query structure.
- **Dynamic JOIN generation** based on required fields.
- **Optimized CTE usage** to avoid redundant computations.

---

## Key Components of SQL Query Composition

### 1. **Query Composition**
Instead of executing multiple queries, FraiseQL composes a single query that retrieves all required data at once. For example, fetching all posts with authors becomes:

```sql
WITH authors AS (
    SELECT id, name FROM authors WHERE id IN (
        SELECT author_id FROM posts WHERE published = true
    )
)
SELECT p.id, p.title, a.name
FROM posts p
JOIN authors a ON p.author_id = a.id
WHERE p.published = true;
```

### 2. **Intelligent JOIN Strategies**
FraiseQL avoids unnecessary JOINs by analyzing which fields are actually requested. For instance, if the client only needs the post title and author name, it won’t JOIN the comments table unless requested.

### 3. **CTEs for Readability and Performance**
CTEs help break down complex queries into logical steps. For example:

```sql
WITH popular_posts AS (
    SELECT id, title
    FROM posts
    WHERE views > 1000
    ORDER BY views DESC
    LIMIT 10
),
authors AS (
    SELECT id, name FROM authors
)
SELECT pp.title, a.name
FROM popular_posts pp
JOIN authors a ON pp.author_id = a.id;
```

### 4. **Subqueries for Filtering**
Subqueries can filter data more efficiently than JOINs in some cases. For example:

```sql
SELECT *
FROM posts
WHERE author_id IN (
    SELECT id FROM authors WHERE location = 'New York'
);
```

---

## Practical Code Examples

Let’s walk through a step-by-step example using FraiseQL to fetch nested data efficiently.

### Example: Fetching Blog Posts with Authors and Comments

#### Problem: Naive Approach (N+1 Queries)
```python
# Pseudocode for naive approach
posts = db.query("SELECT * FROM posts WHERE published = true")
for post in posts:
    author = db.query("SELECT * FROM authors WHERE id = ?", [post.author_id])
    comments = db.query("SELECT * FROM comments WHERE post_id = ?", [post.id])
    print(f"Post: {post.title}\nAuthor: {author.name}\nComments: {[c.content for c in comments]}")
```

This generates **3 queries per post**, leading to N+1 problems.

#### Solution: FraiseQL-Composed Query
FraiseQL would generate:

```sql
WITH posts AS (
    SELECT id, title, author_id
    FROM posts
    WHERE published = true
),
authors AS (
    SELECT id, name FROM authors WHERE id IN (
        SELECT author_id FROM posts
    )
),
comments AS (
    SELECT id, post_id, content FROM comments
    WHERE post_id IN (
        SELECT id FROM posts
    )
)
SELECT
    p.title,
    a.name,
    json_agg(c.content) AS comments
FROM posts p
JOIN authors a ON p.author_id = a.id
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY p.id, a.name;
```

### Key Optimizations in This Query:
1. **CTEs** for each entity (`posts`, `authors`, `comments`).
2. **Single JOIN** between posts and authors.
3. **LEFT JOIN** for comments, avoiding N+1.
4. **JSON aggregation** (or similar) to collect comments in one pass.
5. **Filtering** applied early to reduce the working set.

---

## Implementation Guide: How to Adopt SQL Query Composition

### Step 1: Analyze Your Query Patterns
Start by identifying the most common query shapes in your API:
- Are you fetching lists of items with related data?
- Do clients often request nested structures (e.g., posts + comments + tags)?

### Step 2: Choose a Composition Framework
FraiseQL is one option, but you can implement similar logic manually or use libraries like:
- [Prisma](https://www.prisma.io/) (for TypeScript/Node.js)
- [Django ORM’s prefetch_related](https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related) (for Python)
- Custom SQL generators (e.g., using SQLAlchemy’s Core for Python).

### Step 3: Design Your Schema for Composition
- **Normalize tables** for optimal JOINs.
- **Denormalize when needed** (e.g., store comment counts in the posts table if frequently accessed).
- **Use CTEs** for complex queries (supported in PostgreSQL, MySQL 8+, SQL Server).

### Step 4: Implement the Query Composer
Here’s a high-level approach to building a FraiseQL-like composer:

#### Pseudocode for a Query Composer
```python
class QueryComposer:
    def __init__(self, db_schema):
        self.schema = db_schema

    def compose(self, query_structure):
        # Parse the requested structure (e.g., {'posts': {'author': True, 'comments': True}})
        # Generate CTEs for each level
        # Join tables intelligently
        # Apply filters
        # Return optimized SQL
        pass
```

#### Example Implementation (Simplified)
```python
def compose_posts_with_authors_and_comments(db, published_only=True):
    cte_posts = """
    WITH posts AS (
        SELECT id, title, author_id
        FROM posts
        {}
    )
    """.format("WHERE published = true" if published_only else "")

    cte_authors = """
    authors AS (
        SELECT id, name FROM authors WHERE id IN (
            SELECT author_id FROM posts
        )
    )
    """

    cte_comments = """
    comments AS (
        SELECT id, post_id, content FROM comments
        WHERE post_id IN (
            SELECT id FROM posts
        )
    )
    """

    sql = f"""
    {cte_posts}
    {cte_authors}
    {cte_comments}

    SELECT
        p.id,
        p.title,
        a.name,
        json_agg(c.content) AS comments
    FROM posts p
    JOIN authors a ON p.author_id = a.id
    LEFT JOIN comments c ON p.id = c.post_id
    GROUP BY p.id, a.name;
    """
    return db.execute(sql)
```

### Step 5: Test and Benchmark
- Compare performance of the composed query vs. the naive approach.
- Use tools like `EXPLAIN ANALYZE` (PostgreSQL) to check query plans.
- Gradually roll out to production with canary releases.

---

## Common Mistakes to Avoid

### 1. **Over-JOINing**
   - **Problem**: JOIN-ing every table you can think of, even if the data isn’t needed.
   - **Solution**: Only JOIN tables that are explicitly requested in the query.

### 2. **Ignoring the Database Optimizer**
   - **Problem**: Writing queries the "logical" way (e.g., nested subqueries) instead of letting the optimizer handle the heavy lifting.
   - **Solution**: Rewrite queries to leverage CTEs, JOINs, or laterals where appropriate.

### 3. **Not Using CTEs for Complex Logic**
   - **Problem**: Trying to write everything in a single huge query without breaking it into steps.
   - **Solution**: Use CTEs to modularize complex queries.

### 4. **Forgetting to Filter Early**
   - **Problem**: Applying filters at the end of a query, allowing the database to process unnecessary rows.
   - **Solution**: Filter as early as possible in the query (e.g., in CTEs or WHERE clauses).

### 5. **Assuming All Databases Support the Same Syntax**
   - **Problem**: Writing queries that rely on PostgreSQL-specific features (e.g., `json_agg`) and deploying to MySQL.
   - **Solution**: Use ANSI SQL where possible and add database-specific wrappers if needed.

---

## Key Takeaways

- **SQL Query Composition** solves N+1 and inefficient JOIN problems by combining queries intelligently.
- **FraiseQL** (or similar patterns) uses CTEs, subqueries, and JOINs to fetch nested data in a single optimized query.
- **Key optimizations**:
  - Avoid N+1 by joining related data in one query.
  - Use CTEs to break down complex logic.
  - Filter early to reduce the working set.
- **Tradeoffs**:
  - **Pros**: Faster queries, lower latency, better scalability.
  - **Cons**: More complex queries to write/maintain; requires careful analysis of query shapes.
- **Tools**: Leverage frameworks like Prisma, Django ORM’s prefetch_related, or build your own composer.

---

## Conclusion

SQL Query Composition is a powerful pattern for building high-performance APIs that avoid the pitfalls of N+1 queries and inefficient JOINs. By analyzing your query patterns and composing them intelligently—whether using FraiseQL, Prisma, or a custom solution—you can dramatically improve the speed and scalability of your backend.

The key takeaway? **Don’t let your database work harder than it needs to.** With SQL Query Composition, you’re not just optimizing individual queries; you’re redesigning how your API interacts with data—making it faster, more predictable, and easier to scale.

Try it out in your next project. Start small—compose a few queries manually—and watch the performance improve. Over time, you’ll see that a little upfront effort in query design pays off in massive gains in runtime efficiency.

---

### Further Reading
- [PostgreSQL EXPLAIN ANALYZE](https://www.postgresql.org/docs/current/using-explain.html)
- [Prisma’s Query Composition](https://www.prisma.io/docs/concepts/components/prisma-client/querying-relationships)
- [GraphQL Performance Antipatterns](https://www.howtographql.com/basics/5-performance-antipatterns/)
```