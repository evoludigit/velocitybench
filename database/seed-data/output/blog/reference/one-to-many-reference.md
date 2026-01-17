---

# **[Pattern] One-to-Many Relationships & Cascading Reference Guide**

---

## **Overview**
One-to-many relationships model scenarios where a single record in one table is associated with multiple records in another table. Common examples include:
- A **user** owning **many posts**
- A **department** managing **many employees**
- An **order** containing **many line items**

This pattern ensures data integrity through **foreign keys**, optimizes performance with **cascading actions**, and mitigates **N+1 query problems** via **eager loading** or **batch fetching**. Proper implementation requires careful selection of **cascading rules** (e.g., `ON DELETE CASCADE` for soft/deep deletes) and efficient query strategies to avoid redundant database hits.

---

## **Core Components**
| **Component**       | **Definition**                                                                 | **Example (SQL)**                                                                 |
|---------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Parent Table**    | The "one" side (e.g., `users`, `departments`).                               | `users (id, name)`                                                            |
| **Child Table**     | The "many" side (e.g., `posts`, `employees`).                                 | `posts (id, user_id, title)`                                                  |
| **Foreign Key**     | Column referencing the parent’s primary key.                                  | `ALTER TABLE posts ADD COLUMN user_id INT REFERENCES users(id)`                |
| **Cascading Actions**| Automatically update/delete child records when parent changes.               | `ON UPDATE CASCADE`, `ON DELETE SET NULL`, `ON DELETE CASCADE`                |
| **Indexing**        | Improves performance on foreign key lookups.                                | `CREATE INDEX idx_posts_user_id ON posts(user_id)`                           |
| **Eager Loading**   | Retrieves child records in a single query to avoid N+1 problems.             | **ActiveRecord**: `User.includes(:posts).find(1)`                             |
| **Bulk Operations** | Updates/inserts child records in batches (e.g., via `LIMIT`/`OFFSET` or CTEs).| **SQL**:
```sql
INSERT INTO posts (user_id, title)
SELECT user_id, 'New Post' FROM users LIMIT 10; -- Bulk insert
```

---

## **Schema Reference**
### **Basic One-to-Many Schema**
```sql
-- Parent table
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Child table with FK and optional cascading
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    department_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE CASCADE  -- Delete employees if department is deleted
        ON UPDATE CASCADE  -- Update FK if department ID changes
);

-- Index for performance
CREATE INDEX idx_employees_department_id ON employees(department_id);
```

### **Soft Delete Example**
```sql
-- Parent table with soft delete
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    deleted_at TIMESTAMP NULL,
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- Child table with soft delete cascade
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT fk_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON DELETE CASCADE  -- Cascade soft delete to items
);
```

---

## **Cascading Rules**
| **Rule**               | **Behavior**                                                                 | **Use Case**                                  |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| `ON DELETE CASCADE`     | Deletes all child records when parent is deleted.                          | Permanent one-to-many (e.g., `posts` → `comments`). |
| `ON DELETE SET NULL`   | Sets FK to `NULL` (parent must allow `NULL`).                               | Optional relationships (e.g., `profiles` → `addresses`). |
| `ON DELETE RESTRICT`   | Blocks deletion if child records exist (default).                          | Critical data (e.g., `users` → `accounts`).   |
| `ON UPDATE CASCADE`    | Updates FK if parent’s PK changes (rarely used).                            | Legacy systems with changing IDs.             |

**Warning**: Use `ON DELETE CASCADE` judiciously—it can lead to unintended data loss. Prefer soft deletes (`deleted_at` timestamp) for recoverable operations.

---

## **Query Examples**
### **1. Basic Queries**
#### **Fetch Parent with Children (Eager Loading)**
- **ActiveRecord (Ruby on Rails)**:
  ```ruby
  user = User.includes(:posts).find(1)  # Single query for user + posts
  ```
- **SQLAlchemy (Python)**:
  ```python
  from sqlalchemy.orm import joinedload
  user = session.query(User).options(joinedload(User.posts)).first()
  ```
- **Raw SQL (JOIN)**:
  ```sql
  SELECT users.*, posts.*
  FROM users
  LEFT JOIN posts ON users.id = posts.user_id;
  ```

#### **Fetch Children with Parent Data**
```sql
SELECT posts.*, users.name AS user_name
FROM posts
INNER JOIN users ON posts.user_id = users.id;
```

---

### **2. Aggregations**
#### **Count Children per Parent**
```sql
-- SQL
SELECT departments.id, departments.name, COUNT(employees.id) AS employee_count
FROM departments
LEFT JOIN employees ON departments.id = employees.department_id
GROUP BY departments.id;

-- ActiveRecord
Department.group(:id).count(:employees)
```

#### **Sum Values in Child Table**
```sql
-- SQL
SELECT departments.id, SUM(employees.salary) AS total_salary
FROM departments
LEFT JOIN employees ON departments.id = employees.department_id
GROUP BY departments.id;

-- Django (Python)
from django.db.models import Sum
Department.objects.annotate(total_salary=Sum('employees__salary'))
```

---

### **3. Bulk Operations**
#### **Bulk Insert (Parent + Children)**
```sql
-- Insert parent, then child in one transaction
INSERT INTO departments (name) VALUES ('Engineering'), ('Marketing')
RETURNING id;

-- Use returned IDs to insert children
INSERT INTO employees (department_id, name)
VALUES
    (1, 'Alice'), (1, 'Bob'), (2, 'Charlie');
```

#### **Bulk Update Children**
```sql
-- Update all posts by a user
UPDATE posts
SET title = CONCAT(title, ' (Updated)')
WHERE user_id = 1;
```

---

### **4. Handling N+1 Problems**
#### **Problematic Query (N+1)**
```ruby
# Rails: Each post.load! triggers a separate query
posts = User.find(1).posts
posts.each { |p| p.load!(:comments) }  # 1 (user) + 10 (posts) + 10*5 (comments) = 51 queries
```

#### **Solution: Eager Load**
```ruby
# Single query for user, posts, and comments
user = User.includes(:posts => :comments).find(1)
```

#### **Database-Level Fix (Materialized Path)**
```sql
-- Pre-aggregate data (e.g., daily posts per user)
CREATE MATERIALIZED VIEW user_post_counts AS
SELECT user_id, COUNT(*) AS post_count
FROM posts
GROUP BY user_id;
```

---

## **Performance Considerations**
| **Issue**               | **Symptom**                          | **Solution**                                                                 |
|--------------------------|--------------------------------------|-----------------------------------------------------------------------------|
| **N+1 Queries**          | Slow applications due to repeat DB hits. | Use eager loading (e.g., `includes`, `preload`).                          |
| **Large Child Tables**   | Slow JOINs or aggregations.           | Add indexes on foreign keys (`idx_posts_user_id`).                          |
| **Cascading Overhead**   | Deleting a parent triggers many deletions. | Use `ON DELETE SET NULL` or soft deletes.                                  |
| **Concurrent Writes**    | Race conditions during bulk updates.   | Use transactions (`BEGIN`/`COMMIT`) or database locks.                     |
| **Memory Limits**        | Loading large datasets in memory.     | Use cursors (e.g., `LIMIT/OFFSET` pagination) or streaming APIs.            |

---

## **Related Patterns**
1. **[Many-to-Many Relationships](https://example.com/many-to-many)**
   - Use intermediate tables (e.g., `users_roles`) when a relationship is flexible.
   - Example: `users` ↔ `roles` via `user_roles` (with `user_id`, `role_id` FKs).

2. **[Soft Deletes](https://example.com/soft-deletes)**
   - Replace `DELETE` with a `deleted_at` timestamp for recoverable operations.
   - Example: `ON DELETE CASCADE` → `ON DELETE SET NULL` + `deleted_at` column.

3. **[Batch Processing](https://example.com/batch-processing)**
   - Process large datasets in chunks (e.g., `LIMIT 1000` per batch) to avoid timeouts.
   - Example: Update 10,000 records in 10 batches of 1,000.

4. **[Event Sourcing](https://example.com/event-sourcing)**
   - Track changes via events instead of direct DB updates (useful for auditing cascades).
   - Example: Log `PostCreatedEvent` when a parent record is added.

5. **[GraphQL Relationships](https://example.com/graphql-relationships)**
   - Resolve one-to-many relationships in resolvers to avoid over-fetching.
   - Example:
     ```graphql
     type User { id: ID, posts: [Post!]! }
     type Query { user(id: ID!): User }
     ```
     (Resolve `posts` in the `User` resolver with eager loading.)

---

## **Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                 | **Fix**                                                                 |
|---------------------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **Unindexed Foreign Keys**      | Slow JOINs and poor performance.                                         | Add indexes: `CREATE INDEX idx_table_fk_column ON table(fk_column)`. |
| **Deep Cascading**              | Accidental mass deletions (e.g., `ON DELETE CASCADE` chaining).         | Use `ON DELETE SET NULL` or soft deletes.                              |
| **Lazy Loading Everywhere**     | N+1 problems in high-traffic apps.                                      | Prefer eager loading for critical paths.                             |
| **Ignoring Transaction Isolation** | Dirty reads during bulk updates.                                    | Use `BEGIN TRANSACTION`/`COMMIT` for critical operations.           |
| **Overusing `JOIN` in Queries** | Cartesian products or slow queries.                                     | Filter early (e.g., `WHERE` before `JOIN`).                          |

---

## **Tools & Libraries**
| **Framework**       | **Feature**                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Rails**           | `includes`, `preload`, `eager_load` for N+1 fixes.                          |
| **Django**          | `prefetch_related`, `select_related`, `annotate`.                          |
| **Entity Framework**| `Include` (C#), `withMany` (ASP.NET Core).                                |
| **Hibernate**       | `@OneToMany(fetch = FetchType.EAGER)` to avoid lazy loading pitfalls.      |
| **Prisma (JS)**     | `include` for eager loading (e.g., `post.findUnique({ include: { comments: true } })`). |

---

## **Example: Full User-Posts Implementation**
### **Schema**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_posts_user_id (user_id)
);
```

### **CRUD Operations**
#### **Create (with Post)**
```ruby
# Rails
user = User.create!(username: 'john_doe')
post = user.posts.create!(title: 'Hello World', body: 'First post!')
```

#### **Read (Eager Load)**
```python
# Django
user = User.objects.prefetch_related('posts').get(username='john_doe')
```

#### **Update (Batch)**
```sql
-- SQL
UPDATE posts
SET title = 'Updated Title'
WHERE user_id = 1;
```

#### **Delete (Cascading)**
```ruby
# Rails
user = User.find(1)
user.destroy!  # Deletes user AND all associated posts (due to `ON DELETE CASCADE`)
```

---
**Note**: Always test cascading behavior in a staging environment. Consider adding validation (e.g., `before_destroy` hooks) to prevent accidental deletes.