# **[Pattern] ORM & Database Access Patterns Reference Guide**

---

## **Overview**
Object-Relational Mapping (ORM) abstracts database interactions by modeling database tables as Python classes, enabling CRUD operations via intuitive object-oriented syntax. While ORMs (e.g., SQLAlchemy, Django ORM, Django ORM) simplify development, improper usage can lead to performance bottlenecks, inefficient queries, or tightly coupled code. This guide outlines best practices for structuring ORM architectures, optimizing query performance, and avoiding anti-patterns like N+1 queries, eager vs. lazy loading pitfalls, and excessive ORM usage. It covers schema design, query optimization, and integration with other patterns (e.g., Repository, Active Record).

---

## **Key Concepts & Implementation Details**

### **1. Core ORM Principles**
| Concept               | Description                                                                                                                                                     | Example Use Case                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Object-Relationship Mapping** | Maps database tables to Python classes with fields, relationships (1:1, 1:M, M:N), and validators.                                                     | User model with `posts` relationship (1:M), `Profile` model linked to `User` (1:1).                |
| **Session Management** | Temporarily tracks changes to objects (additions, deletions, updates) and manages transactions.                                                       | `session.add(user)` → `session.commit()` to persist changes.                                         |
| **Eager vs. Lazy Loading** | Eager loading fetches relationships immediately; lazy loading loads them on demand (can cause N+1 queries).                                         | Use `select_related` (Django) or `joinedload` (SQLAlchemy) for eager loading.                       |
| **Query Building**      | Constructs SQL queries dynamically via ORM APIs (avoids raw SQL where possible).                                                                         | `User.query.filter(User.age > 18).all()` instead of manual `SELECT * FROM users WHERE age > 18`.    |
| **Bulk Operations**    | Processes multiple records in a single query (e.g., bulk insert/update/delete) for performance.                                                      | `User.update().where(User.is_active == False).values(is_active=True)` (SQLAlchemy).               |
| **Caching**            | Reduces database load by caching query results (e.g., Django’s `cache`, SQLAlchemy’s `scoped_session`).                                         | Cache frequent `SELECT` queries with `@cache_page` (Django) or `INDEX_ON` hints.                    |

---

### **2. Schema Design Guidelines**
#### **Table Structure**
- **Primary Keys**: Use auto-incrementing integers or UUIDs (avoid nullable columns as PKs).
- **Foreign Keys**: Enforce referential integrity; prefer `ON DELETE CASCADE` for managed relationships.
- **Indexing**: Add indexes for frequently queried columns (e.g., `email`, `status`).
- **Normalization vs. Denormalization**:
  - Normalize for write-heavy apps (e.g., e-commerce).
  - Denormalize for read-heavy apps (e.g., analytics dashboards) to reduce joins.

#### **Example Schema (SQLAlchemy)**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
```

---

### **3. Query Patterns & Optimization**
#### **Common Query Examples**
| Pattern                  | Description                                                                                                                                 | Code Example (SQLAlchemy/Django)                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Basic Filtering**      | Filter records using predicates.                                                                                                        | `User.query.filter(User.age > 30).all()` (Django)                                                 |
| **Joins**                | Combine tables to fetch related data.                                                                                                     | `Post.query.join(User).filter(User.is_active=True).all()`                                         |
| **Aggregations**         | Compute summary stats (e.g., `COUNT`, `AVG`).                                                                                             | `db.session.query(func.count(Post.id)).filter(Post.author_id == user.id).scalar()` (SQLAlchemy)  |
| **Pagination**           | Retrieve data in chunks (e.g., `LIMIT/OFFSET`).                                                                                        | `User.objects.order_by("email").offset(10).limit(10)` (Django)                                   |
| **Subqueries**           | Use subqueries for dynamic filtering or correlated results.                                                                           | `User.query.filter(User.id.in_(db.session.query(Post.author_id).distinct()))`                    |
| **Bulk Updates**         | Update multiple records atomically.                                                                                                    | `User.update().where(User.status == "inactive").values(status="active").execute()`                |

#### **Performance Anti-Patterns & Fixes**
| Anti-Pattern               | Problem                                                                                     | Solution                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **N+1 Queries**            | Lazy-loading relationships triggers excessive queries.                                       | Use `select_related` (Django) or `joinedload` (SQLAlchemy).                                  |
| **Over-Fetching**          | Loading unnecessary columns (e.g., `SELECT *`).                                             | Explicitly select columns: `User.query.with_entities(User.id, User.email).all()`.               |
| **Raw SQL Abuse**          | Bypassing ORM for simple queries (loses benefits like type safety).                         | Use ORM methods; reserve raw SQL for complex cases.                                             |
| **Uncached Repeated Queries** | Repeating the same query without caching.                                                     | Cache results with `@cache_page` (Django) or `scoped_session`.                               |
| **Deeply Nested Relationships** | Chaining relationships causes performance degradation.                                      | Flatten relationships or use `prefetch_related` (Django).                                     |

---

### **4. Advanced ORM Techniques**
#### **Connection Pooling**
- Configure pool size to handle concurrent connections efficiently:
  ```python
  # SQLAlchemy
  engine = create_engine("postgresql://user:pass@localhost/db",
                         pool_size=10, max_overflow=20)
  ```

#### **Event Listeners**
- Hook into ORM events (e.g., `before_insert`, `after_update`) for cross-cutting concerns:
  ```python
  @event.listens_for(User, 'before_insert')
  def log_user_creation(mapper, connection, target):
      print(f"User {target.email} is being created.")
  ```

#### **Hybrid Properties**
- Combine database columns with Python logic:
  ```python
  full_name = Column(String(100))
  @hybrid_property
  def full_name(self):
      return f"{self.first_name} {self.last_name}"

  @full_name.expression
  def full_name(cls):
      return concat(cls.first_name, ' ', cls.last_name)
  ```

#### **Repository Pattern Integration**
- Decouple business logic from ORM by abstracting queries into a repository:
  ```python
  class UserRepository:
      def get_active_users(self):
          return User.query.filter_by(is_active=True).all()
  ```

---

### **5. Testing ORM Code**
- **Unit Tests**: Mock database sessions using `unittest.mock` or libraries like `pytest-mock`.
  ```python
  from unittest.mock import MagicMock

  def test_user_creation():
      session = MagicMock()
      user = User(email="test@example.com")
      session.add(user)
      session.commit.assert_called_once()
  ```
- **Integration Tests**: Use test databases (e.g., SQLite in-memory) to verify ORM behavior:
  ```python
  # Django
  from django.test import TestCase

  class UserModelTest(TestCase):
      def test_user_creation(self):
          user = User.objects.create(email="test@example.com")
          self.assertEqual(user.email, "test@example.com")
  ```

---

## **Related Patterns**
| Pattern Name               | Description                                                                                                                                                     | Integration Points                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Repository Pattern**     | Abstracts data access logic behind an interface, promoting testability and loose coupling.                                                              | Replace ORM calls in services/repositories with repository methods.                                     |
| **Active Record**          | Combines model and data access in a single class (e.g., Django models).                                                                                 | Use ORM models as Active Records for simple CRUD applications.                                         |
| **Unit of Work**           | Manages transactions and object state changes (complements ORM sessions).                                                                              | Integrate with ORM sessions to batch operations (e.g., `session.commit()`).                           |
| **CQRS**                   | Separates read and write models (query models vs. command models).                                                                                     | Use ORM for writes; optimize read models with denormalized tables or NoSQL for analytical queries.   |
| **Pagination & Caching**   | Reduces database load for large datasets.                                                                                                             | Cache paginated results or use read replicas for read-heavy patterns.                                 |
| **Event Sourcing**         | Stores state changes as an immutable event log.                                                                                                        | Append-only schema; store ORM objects as events (e.g., `UserCreated`).                                  |

---

## **Best Practices Summary**
1. **Avoid Raw SQL**: Prefer ORM methods for type safety and maintainability.
2. **Batch Operations**: Use bulk `INSERT/UPDATE/DELETE` for large datasets.
3. **Lazy Loading**: Be cautious—prefetch relationships when needed to avoid N+1 queries.
4. **Index Strategically**: Add indexes to columns used in `WHERE`, `JOIN`, or `ORDER BY` clauses.
5. **Test Database-Specific Behavior**: ORM behavior may vary across databases (e.g., PostgreSQL vs. MySQL).
6. **Monitor Queries**: Use ORM logging or tools like `django-debug-toolbar` to identify slow queries.
7. **Leverage Caching**: Cache frequent queries or entire model instances.
8. **Decouple Logic**: Use the Repository or Unit of Work pattern to isolate ORM details.

---
**See also**:
- [ORM Pitfalls & Solutions](https://docs.sqlalchemy.org/en/14/orm/pitfalls.html)
- [Django ORM Best Practices](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [SQLAlchemy Advanced Usage](https://docs.sqlalchemy.org/en/14/orm/advanced_load.html)