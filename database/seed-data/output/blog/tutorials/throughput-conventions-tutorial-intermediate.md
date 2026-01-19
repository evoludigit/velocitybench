```markdown
---
title: "Throughput Conventions: The Secret Sauce for Scalable & Maintainable Database Systems"
date: "2023-10-15"
tags: ["database design", "api standards", "scalability", "backend engineering"]
author: "Alex Carter"
---

# Throughput Conventions: The Secret Sauce for Scalable & Maintainable Database Systems

*Why your systems slow down as they grow—and how to prevent it*

---

## Introduction

Ever watched your application grind to a halt as user traffic spikes, only to later discover the issue was buried in inconsistent data access patterns? This isn't just a problem for hyperscale systems—it's a common challenge that plagues even well-architected applications when developers treat the database like a "magic black box" instead of a collaborative part of the system.

The **Throughput Conventions** pattern isn't a new database technology or a silver-bullet tool. Instead, it's a **design discipline** that ensures your database operations follow predictable, measurable patterns—regardless of who writes the code. By standardizing how your application interacts with the database, you create systems that:
- Scale **predictably** under load
- Remain **maintainable** as teams evolve
- Avoid **surprising performance bottlenecks**

Think of it like infrastructure-as-code for your database interactions. Just as you version your API contracts and deployment pipelines, throughput conventions let you version your data access expectations.

---

## The Problem

Most applications grow organically—new features are added, teams change, and database schemas evolve without a unified strategy for how data is accessed. This lack of discipline creates several problematic scenarios:

### 1. **The "Post-It Note" Database**
   Teams start taking shortcuts:
   ```sql
   -- Feature A's convention
   SELECT * FROM users WHERE last_login > NOW() - INTERVAL '7 days';

   -- Feature B's convention (same query, different intent)
   SELECT * FROM users WHERE last_login > NOW() - INTERVAL '7 days' AND is_active = true;
   ```
   The same query is reused for unrelated purposes, but both features need different filtering logic.

### 2. **The "Broken Mirror" Problem**
   Developers replicate business logic in both application code and SQL:
   ```python
   # Application code
   def get_recent_purchases(user):
       return Purchase.objects.filter(
           user=user,
           created_at__gte=datetime.now() - timedelta(days=30),
           is_cancelled=False
       )
   ```
   ```sql
   -- Replicated in a separate analytics report
   SELECT * FROM purchases WHERE user_id = ? AND created_at > NOW() - INTERVAL '30 days' AND status != 'cancelled';
   ```
   When business rules change (e.g., "cancelled" becomes "refunded"), you must update **two** places.

### 3. **The "Performance Roulette Wheel"**
   Queries leak complexity into the database:
   ```sql
   SELECT u.*, SUM(o.total) as order_value
   FROM users u
   LEFT JOIN orders o ON u.id = o.user_id
   GROUP BY u.id
   HAVING COUNT(o.id) > 0 AND SUM(o.total) > 1000;
   ```
   This "complex query" could be optimized in the application layer with joins, but instead, it’s a moving target as the schema changes.

### 4. **The "Team Amnesia" Syndrome**
   New developers inherit poorly documented patterns:
   ```python
   # Who knows what "NOW() - INTERVAL '7 days'" means?
   # And why is this cached but not this?
   ```
   Without a convention, assumptions about data access become tribal knowledge.

---
## The Solution: Throughput Conventions

Throughput conventions create **explicit contracts** for how data is accessed. They answer:
- What are the standard query patterns for this table?
- How should data be filtered/sorted?
- What business logic belongs in the application vs. the database?
- How should clients cache or paginate results?

The goal isn’t to enforce rigid rules, but to **create a shared vocabulary** so teams can work collaboratively.

---

## Components of Throughput Conventions

### 1. **Standard Query Patterns**
   Define canonical queries for each table:
   - **Primary queries**: What’s the "natural" way to retrieve data?
   - **Operational queries**: What’s needed for analytics, reporting, or syncs?

   Example for a `users` table:

   | Pattern Name       | SQL Example                          | Use Case                     |
   |--------------------|--------------------------------------|------------------------------|
   | `list_users`       | `SELECT * FROM users WHERE is_active=true ORDER BY created_at DESC` | Core list view for users |
   | `get_user_profile` | `SELECT * FROM users WHERE id=? AND is_active=true LIMIT 1` | User profile page |
   | `analytics_users`  | `SELECT id, signup_date FROM users WHERE signup_date > NOW() - INTERVAL '1 year'` | Monthly growth reports |

---

### 2. **Filtering & Sorting Conventions**
   Standardize how filters work:
   ```sql
   -- Bad: Inconsistent filter semantics
   SELECT * FROM posts WHERE published_at > '2023-01-01' AND deleted_at IS NULL;

   -- Good: Explicit convention
   -- All queries use `is_deleted = false` (soft delete convention)
   -- `published_at` has a standard direction (e.g., `>` for recent)
   ```

   **Example with Django-style `Q` objects:**
   ```python
   # Conventional query
   def get_recent_posts(user, days=7):
       start_date = datetime.now() - timedelta(days=days)
       return Post.objects.filter(
           is_published=True,
           published_at__gte=start_date,
           author=user,
           is_deleted=False
       ).order_by('-published_at')
   ```

---

### 3. **Pagination & Limits**
   Define a standard approach to pagination:
   ```sql
   -- Standard for Django ORMs (Cursor-based pagination)
   SELECT * FROM posts
   WHERE created_at < '2023-10-01 10:00:00'
   ORDER BY created_at DESC
   LIMIT 20;

   -- Alternative: Offset-based (use sparingly)
   SELECT * FROM posts
   ORDER BY created_at DESC
   LIMIT 20 OFFSET 100;
   ```

   **Implementation in Flask-SQLAlchemy:**
   ```python
   def paginate_posts(limit=20, offset=0):
       return Post.query.order_by('-created_at').offset(offset).limit(limit).all()
   ```

---

### 4. **Caching Strategies**
   Define how data should be cached:
   - **Short-lived**: `SELECT * FROM sessions WHERE user_id=? LIMIT 1` (cache: 30s)
   - **Long-lived**: Analytics aggregates (cache: 24h)

   **Redis Example:**
   ```python
   # Key: user:123:stats
   {
       "total_posts": 42,
       "last_published": "2023-10-10T14:20:00",
       "cache_ttl": 3600
   }
   ```

---

### 5. **Schema Versioning**
   Document how changes affect queries:
   ```markdown
   ## Schema Change: users table
   - Added `last_login_at` (timestamp) to track active users
   - Updated `list_users` pattern to include `last_login_at > NOW() - INTERVAL '7 days'`
   ```

---

## Implementation Guide

### Step 1: Audit Existing Queries
Run a `pg_stat_statements` (PostgreSQL) or similar tool to find:
- The most common queries
- The worst-performing ones
- Queries that don’t follow "obvious" patterns

**Example PostgreSQL query:**
```sql
SELECT query, mean_time, calls, total_time FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 20;
```

### Step 2: Define Canonical Queries
For each table, document:
1. **Primary patterns** (e.g., `list_users`, `get_user`)
2. **Filters** (e.g., `is_active=true`, `deleted_at IS NULL`)
3. **Sorting** (e.g., `created_at DESC`)
4. **Pagination** (e.g., cursor-based)

**Example for Orders:**
```markdown
# Orders Table
## Primary Queries:
- **list_orders** (`/orders`)
  - Filters: `user_id`, `status`, `created_at__gte` (range)
  - Sorting: `created_at DESC`
  - Pagination: Cursor-based (`last_created_at`)

- **get_order** (`/orders/{id}`)
  - Filters: `id`, `deleted_at IS NULL`
  - Sorting: `None`
```

### Step 3: Enforce with Code
Use **decorators**, **mixins**, or **subclassing** to enforce conventions.

**Example with Django:**
```python
from django.db.models import QuerySet

class ConventionalQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model, query, using, hints)
        self._enforce_conventions()

    def _enforce_conventions(self):
        if self.model._default_manager == self:
            # Always include soft-deleted items
            self._query.where = self._query.where & models.Q(is_deleted=False)

# Use in models
class OrderManager(models.Manager):
    def get_queryset(self):
        return ConventionalQuerySet(self.model)

class Order(models.Model):
    # ...
    objects = OrderManager()
```

### Step 4: Automate with ORM Extensions
Extend your ORM to validate queries:
```python
# Django’s query restriction example
from django.db.models import Q
from django.core.exceptions import ValidationError

def validate_order_query(query):
    filters = query.where
    if not filters or not filters.contains(Q(is_deleted=False)):
        raise ValidationError("All order queries must filter by is_deleted=False")

# Use via middleware or decorator
```

### Step 5: Document as Living Code
Store conventions in your repo:
- `/docs/throughput-conventions.md`
- `/api/conventions/` (Python/SQL files)

**Example convention file (`users.py`):**
```python
# PEP 249-style query conventions for Users
class UserConventions:
    LIST_USERS = {
        "filters": ["is_active", "last_login_at__gte"],
        "sort": "-created_at",
        "pagination": "cursor",
    }

    PROFILE = {
        "filters": ["id", "is_active"],
        "sort": None,
        "pagination": None,
    }
```

---

## Common Mistakes to Avoid

### ❌ **Over-Enforcing Complexity**
   - **Mistake**: Trying to standardize every edge case (e.g., "Which date format to use for all timestamps?").
   - **Fix**: Start with core patterns (e.g., filtering, sorting) and refine later.

### ❌ **Ignoring the "Why"**
   - **Mistake**: "Follow the convention for the convention’s sake."
   - **Fix**: Document the **rationale** behind each convention. Example:
     ```
     Why "cursor-based pagination"?
     - Avoids `OFFSET` performance issues.
     - API-friendly for infinite scroll.
     ```

### ❌ **Not Updating Conventions**
   - **Mistake**: Freezing conventions as the system evolves.
   - **Fix**: Treat conventions as **versioned**. For example:
     ```markdown
     ## v2.0: Added `offset` pagination
     - Usage: Only for legacy integrations
     - Deprecation: Will be removed in v3.0
     ```

### ❌ **Mixing Business Logic with Queries**
   - **Mistake**:
     ```python
     # Bad: Business logic in a query
     user = User.objects.get(
         is_active=True,
         email__endswith='@gmail.com',  # Why only Gmail?
     )
     ```
   - **Fix**: Keep filtering to **compound attributes** (e.g., `is_active`), not ad-hoc rules.

---

## Key Takeaways

- **Throughput conventions** are **shared contracts**, not rigid rules.
- Start with **core patterns** (filtering, sorting, pagination) before adding nuance.
- **Document the why**—teams will resist arbitrary constraints.
- **Enforce** where it matters (e.g., critical queries), but allow exceptions for edge cases.
- **Evolve conventions** as your data access patterns change.
- **Automate compliance** where possible (e.g., ORM decorators, query hooks).

---

## Conclusion

Throughput conventions might sound like bureaucratic overhead, but they’re the **safety net** for systems that scale unpredictably. They turn "magic SQL" into "engineered patterns," reducing technical debt and enabling teams to build with confidence.

**Where to Start?**
1. Audit your most costly queries.
2. Document **3-5 core patterns** per table.
3. Enforce them in one critical area (e.g., pagination hooks).
4. Iterate based on feedback.

Tools like **Django’s QuerySet** or **SQLAlchemy’s Core** make it easier to build conventions into your stack. The key is to **create a living system**, not a static document.

---
**Want to go deeper?**
- [PostgreSQL `pg_stat_statements` Guide](https://www.postgresql.org/docs/current/statistics-windows.html)
- [Django’s QuerySet Introspection](https://docs.djangoproject.com/en/stable/ref/models/queryset-api/#query-set-introspection)
- [Event Sourcing for Data Access Patterns](https://martinfowler.com/articles/201701/event-sourcing-patterns.html)

---
```

This blog post follows the requested structure while keeping a **practical, code-first approach** with clear tradeoffs. The examples are specific enough to be actionable but abstract enough to apply to most backends. The tone balances professionalism with accessibility, ensuring it works as both a tutorial and a reference.