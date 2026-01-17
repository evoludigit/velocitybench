```markdown
# The `fk_*` Naming Pattern: How FraiseQL Makes Foreign Keys Clear and Performant

**May 10, 2024 • 12 min read**

---

## Introduction

As backend engineers, we spend a significant portion of our time designing and maintaining database schemas—often juggling readability, performance, and long-term maintainability. Foreign keys (FKs) are a cornerstone of relational databases, enforcing referential integrity and defining relationships between tables. But how we *name* those foreign keys can make a world of difference in how maintainable and performant our database code becomes.

At Fraise, we’ve adopted a disciplined approach to foreign key naming: **always prefix foreign key columns with `fk_*` and reference surrogate primary keys (`pk_*`)**. This pattern isn’t new, but it’s rarely documented in depth—especially with concrete examples and tradeoff discussions. Even companies like Uber and Stripe have evolved their naming conventions, but few explain *why* the `fk_*` prefix stands out as a best practice.

In this post, I’ll break down why this naming convention matters, how it improves code clarity and query performance, and what it means to implement it consistently. We’ll also explore what happens when you deviate from the pattern and how to avoid common pitfalls.

---

## The Problem: Unclear Foreign Key Relationships and Poor JOIN Performance

Let’s start with a hypothetical example to illustrate the chaos that can arise from inconsistent foreign key naming.

### Example: A Messy Schema

Here’s a schema where foreign keys are named arbitrarily:

```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    post_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255),
    content TEXT,
    author_id INT,  -- FK to users.user_id, but what about the column name?
    likes INT DEFAULT 0
);

-- This is a FK to posts.post_id, but the column is named `commenter`
CREATE TABLE comments (
    comment_id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT,
    commenter INT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- This FK is named `user_id` but references `posts.post_id`
CREATE TABLE post_tags (
    tag_id INT PRIMARY KEY AUTO_INCREMENT,
    post_id INT,
    user_id INT,  -- Confusing! It's not a user_id, it's a post_id!
    tag VARCHAR(50)
);
```

Now, let’s say you want to write a query joining these tables:

```sql
SELECT u.username, p.title, c.content, t.tag
FROM users u
JOIN posts p ON u.user_id = p.author_id
JOIN comments c ON p.post_id = c.post_id
JOIN post_tags t ON p.post_id = t.user_id;
```

There’s a problem: **the column name `user_id` in `post_tags` is misleading**. It suggests we’re joining to a user table, but in reality, it’s referencing a post. This ambiguity makes the query harder to write, debug, and maintain.

---

### Performance Issues

Beyond readability, inconsistent foreign key naming can also hurt query performance. Consider a common pattern:

```sql
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,  -- FK to customers.customer_id
    total DECIMAL(10, 2)
);

CREATE TABLE order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,  -- FK to orders.order_id
    product_id INT,  -- FK to products.product_id
    quantity INT
);
```

Now, suppose you often query product details alongside order items, such as:

```sql
SELECT o.order_id, oi.product_id, p.name
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;
```

If you add indexes on those foreign keys (which you should!), great. But what if you’re pulling data from multiple tables with foreign keys named inconsistently? You might end up with something like this:

```sql
-- Hypothetical query with inconsistent column names
SELECT o.order_id, oi.item_order_id, p.product_id
FROM orders o
JOIN order_items oi ON o.order_id = oi.item_order_id
JOIN products p ON oi.product_id = p.product_id;
```

This forces the database engine to rename and reindex columns just to match your query, which can add overhead, especially in large schemas.

---

## The Solution: A Consistent `fk_*` Naming Pattern

Our goal is twofold:
1. **Make foreign key relationships explicit and unambiguous** by using a consistent naming convention.
2. **Optimize JOIN performance** by standardizing on a predictable pattern.

The `fk_*` naming convention solves both problems. Here’s how:

### Core Principles

1. **All foreign keys are prefixed with `fk_`** (e.g., `fk_user_id` instead of `user_id`).
2. **Foreign keys always reference surrogate primary keys (`pk_*`)**. For example, if the primary key of the parent table is `user_id`, the foreign key will be `fk_user_id`. If the primary key is `product_id`, the foreign key will be `fk_product_id`.
3. **Avoid reusing column names** (e.g., never have both `author_id` and `fk_author_id` in the same table).
4. **Surrogate keys are always integers** (e.g., `pk_user_id`). This simplifies JOINs and reduces type mismatches.

---

### Example: A Clean, Standardized Schema

Let’s rewrite the earlier schema using the `fk_*` convention:

```sql
CREATE TABLE users (
    pk_user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    pk_post_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255),
    content TEXT,
    fk_user_id INT NOT NULL,
    likes INT DEFAULT 0,
    FOREIGN KEY (fk_user_id) REFERENCES users(pk_user_id)
);

CREATE TABLE comments (
    pk_comment_id INT PRIMARY KEY AUTO_INCREMENT,
    fk_post_id INT NOT NULL,
    fk_user_id INT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_post_id) REFERENCES posts(pk_post_id),
    FOREIGN KEY (fk_user_id) REFERENCES users(pk_user_id)
);

CREATE TABLE post_tags (
    pk_tag_id INT PRIMARY KEY AUTO_INCREMENT,
    fk_post_id INT NOT NULL,
    fk_user_id INT NOT NULL,
    tag VARCHAR(50),
    FOREIGN KEY (fk_post_id) REFERENCES posts(pk_post_id),
    FOREIGN KEY (fk_user_id) REFERENCES users(pk_user_id)
);
```

Now, let’s rewrite the query using this convention:

```sql
SELECT u.username, p.title, c.content, t.tag
FROM users u
JOIN posts p ON u.pk_user_id = p.fk_user_id
JOIN comments c ON p.pk_post_id = c.fk_post_id
JOIN post_tags t ON p.pk_post_id = t.fk_post_id;
```

The relationship between tables is **immediately obvious**. And because we’re consistently referencing `pk_*` keys, there’s no ambiguity.

---

## Implementation Guide

Now that we’ve seen why the `fk_*` pattern is powerful, let’s discuss how to implement it in your project.

---

### Step 1: Define a Naming Convention

Start by documenting your naming rules:

1. **Surrogate primary keys**: Always named `pk_<table_name>` and are integers (e.g., `pk_user_id`).
2. **Natural primary keys (if used)**: Still named `pk_<table_name>`, but may be strings or UUIDs.
3. **Foreign keys**: Always prefixed with `fk_`, referencing the surrogate primary key of the parent table. For example, if `posts` has `fk_user_id`, it references `users.pk_user_id`.

---

### Step 2: Migrate Existing Databases

If you’re working with an existing database, follow this process:

1. **Backup your database** before making changes.
2. **Rename foreign keys incrementally**:
   - First, add new columns with the `fk_*` prefix.
   - Update application code to use the new column names.
   - Once the new columns are in use, deprecate the old ones.
   - Eventually, drop the old columns.
3. **Update foreign key constraints** to point to `pk_*` columns.

Example migration:

```sql
-- Add the new fk_* column
ALTER TABLE posts ADD COLUMN fk_user_id INT AFTER likes;

-- Update application code to use fk_user_id

-- Add the new foreign key constraint
ALTER TABLE posts ADD CONSTRAINT
    fk_posts_user FOREIGN KEY (fk_user_id) REFERENCES users(pk_user_id);

-- After verifying the new column is in use, you can drop the old column
ALTER TABLE posts DROP COLUMN author_id;
```

---

### Step 3: Enforce the Convention in Code

Update your application code (e.g., ORM, raw SQL, or API layer) to use the new naming convention.

#### Example with Django ORMs

For Django, define models with explicit foreign keys:

```python
from django.db import models

class User(models.Model):
    pk_user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    created_at = models.TimestampField(auto_now_add=True)

class Post(models.Model):
    pk_post_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        db_column='fk_user_id',  # Explicitly define the column name
    )
    likes = models.IntegerField(default=0)

class Comment(models.Model):
    pk_comment_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        db_column='fk_post_id',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='fk_user_id',
    )
    content = models.TextField()
    created_at = models.TimestampField(auto_now_add=True)
```

#### Example with SQLAlchemy

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = MetaData()

# Relationship table
post_tags = Table(
    'post_tags',
    metadata,
    Column('pk_tag_id', Integer, primary_key=True, autoincrement=True),
    Column('fk_post_id', Integer, ForeignKey('posts.pk_post_id')),
    Column('fk_user_id', Integer, ForeignKey('users.pk_user_id')),
    Column('tag', String(50)),
)

class User(Base):
    __tablename__ = 'users'
    pk_user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    created_at = Column(Timestamp, default=func.now())

class Post(Base):
    __tablename__ = 'posts'
    pk_post_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    content = Column(Text)
    fk_user_id = Column(Integer, ForeignKey('users.pk_user_id'))
    likes = Column(Integer, default=0)
```

---

### Step 4: Update Queries and API Responses

Ensure your application logic aligns with the new naming scheme. For example, in a REST API, return data with `fk_*` prefixes:

```json
// Instead of:
{
  "id": 1,
  "author_id": 5,
  "title": "Hello, World!"
}

// Use this:
{
  "pk_post_id": 1,
  "fk_user_id": 5,
  "title": "Hello, World!"
}
```

---

## Common Mistakes to Avoid

While the `fk_*` pattern is powerful, it’s easy to misapply it. Here are common pitfalls:

1. **Mixing natural and surrogate keys inconsistently**
   - Never reference a natural key (e.g., `user.email`) in a foreign key. Always use surrogate keys (e.g., `pk_user_id`).
   - Avoid: `fk_user_email INT REFERENCES users(email)`.
   - Do: `fk_user_id INT REFERENCES users(pk_user_id)`.

2. **Including `fk_*` in API responses unnecessarily**
   - Foreign keys are database internals. Your API should return **only the data your clients need**, not the underlying schema. Use `pk_*` in internal tables but expose meaningful fields in APIs.

3. **Not documenting your convention**
   - If your team isn’t aware of the naming pattern, your changes will be confusing. Document the rules in your README or engineering wiki.

4. **Assuming UUIDs are a good surrogate key**
   - UUIDs are often used for distributed systems, but they’re **not the same as integers**. In our convention, surrogate keys are always integers (e.g., `pk_user_id`). If you must use UUIDs, consider a hybrid approach where UUIDs are the natural key, but you add a surrogate `pk_*` column for performance-critical foreign keys.

5. **Skipping migrations**
   - As mentioned earlier, migrating from old to new column names can be disruptive. Plan for this step carefully, and test thoroughly in staging before production.

---

## Key Takeaways

Here’s a quick recap of why the `fk_*` naming pattern works and how to use it effectively:

- **Explicit relationships**: `fk_*` makes it crystal clear which table a foreign key references.
- **Consistent JOINs**: Always referencing `pk_*` keys simplifies query writing and avoids type mismatches.
- **Better performance**: Standardized foreign keys let the database optimize JOINs more effectively.
- **Avoids ambiguity**: No more confusing column names like `user_id` that reference posts instead of users.
- **Team consistency**: A documented convention reduces context-switching for new engineers.

---

## Conclusion: When to Use `fk_*` and When Not To

The `fk_*` naming pattern is a **strong default** for most relational database schemas, especially if you optimize for readability and consistency. However, like all patterns, it has tradeoffs:

- **Pros**:
  - Clearer schema and queries.
  - Better performance due to consistent JOINs.
  - Easier migration paths for future changes.

- **Cons**:
  - Requires some discipline to enforce.
  - May not fit perfectly with legacy systems.
  - UUIDs can complicate things if you’re not careful.

### When to Avoid or Modify the Pattern

1. **Legacy databases with deep dependencies**: If your database was written by another team with their own conventions, migrating to `fk_*` may be too risky.
2. **External systems with strict schema requirements**: If another service expects a specific column name (e.g., `author_id`), you may need to accommodate that.
3. **Temporary or throwaway projects**: If the project is small or short-lived, the overhead of enforcing `fk_*` may not be worth it.

---

### Final Thoughts

At Fraise, we’ve found that adopting the `fk_*` pattern has made our database schemas **more maintainable** and our JOIN queries **faster**. While no naming convention is perfect, this pattern strikes a balance between clarity, performance, and consistency—making it a valuable tool in your database design toolkit.

Try it in your next project, or gradually migrate your existing database. The benefits in the long run will speak for themselves.

---

**What’s your opinion?** Do you use a similar naming convention? Have you seen benefits or drawbacks we haven’t covered? Share your thoughts on [Twitter](https://twitter.com/your handle) or in the comments below.

Happy coding!
```

---
**Appendix**: More Resources
For further reading, check out:
- [Uber’s Database Design Guide](https://www.uber.com/engineering/2015/05/uber-development-guide-part-2-database)
- [Stripe’s Database Naming Conventions](https://stripe.com/blog/naming-conventions)
- [SQLAlchemy Foreign Key Documentation](https://docs.sqlalchemy.org/en/14/orm/relationships.html#foreign-key-relationships)