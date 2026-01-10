# **[Pattern] Database Relationship Patterns – Reference Guide**

---

## **1. Overview**
Database relationships define how tables interact, ensuring data integrity, minimizing redundancy, and optimizing query performance. Three core relationship types—**one-to-one (1:1)**, **one-to-many (1:N)**, and **many-to-many (M:N)**—form the foundation of relational database design. Proper application of these patterns supports:
- **Normalization** (eliminating redundant data via structured joins).
- **Data consistency** (enforced via foreign keys and constraints).
- **Efficient querying** (reducing redundant data retrieval).

This guide covers schema design, implementation, and query patterns for each relationship type, including best practices for normalization, indexing, and edge cases.

---

## **2. Schema Reference**

| **Relationship** | **Description**                                                                 | **Schema Example**                                                                                     | **Foreign Key Placement**                          | **Constraints**                                  | **Use Case**                                                                                     |
|------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------|------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **One-to-One (1:1)** | A row in Table A links to **one and only one** row in Table B, and vice versa.   | `users(id, name)` ↔ `user_profiles(id, bio)` where `user_profiles.id` references `users.id`.           | Primary key in B references primary key in A.      | `UNIQUE` on foreign key (optional).               | Storing optional, large data (e.g., user photos, tax documents).                             |
| **One-to-Many (1:N)** | A row in Table A links to **zero or many** rows in Table B.                      | `employees(id, manager_id)` where `manager_id` references `employees.id` (a manager may manage many).   | Foreign key in B references primary key in A.     | `ON DELETE CASCADE` (if deletion propagation needed). | Hierarchies (org charts), inventories (orders-items).                                        |
| **Many-to-Many (M:N)** | A row in Table A links to **zero or many** rows in Table B, and vice versa.      | `orders(id)` ↔ `order_items(id, product_id, quantity)` where a junction table `order_items` mediates.  | Two foreign keys (one in A → junction, one in B → junction). | `PRIMARY KEY` on composite keys of junction table.     | Associations (users → roles, courses → students).                                            |

---

## **3. Implementation Details**

### **3.1 One-to-One Relationships**
**When to Use:**
- Pairing primary tables with optional, large, or sensitive data (e.g., `users` ↔ `password_salt`).
- Avoid overuse; prefer separate tables only if data is logically distinct.

**Schema Variations:**
1. **Primary Key Inheritance**:
   ```sql
   CREATE TABLE users (
     id INT PRIMARY KEY,
     name VARCHAR(100)
   );

   CREATE TABLE user_profiles (
     id INT PRIMARY KEY,  -- Saves space by reusing `users.id`
     bio TEXT,
     FOREIGN KEY (id) REFERENCES users(id)
   );
   ```
   - *Pros*: Saves storage; simpler joins.
   - *Cons*: Deleting a user also deletes their profile.

2. **Composite Key**:
   ```sql
   CREATE TABLE user_profiles (
     user_id INT NOT NULL,
     bio TEXT,
     PRIMARY KEY (user_id),
     FOREIGN KEY (user_id) REFERENCES users(id)
   );
   ```
   - *Pros*: Explicit separation; avoids accidental deletions.
   - *Cons*: Slightly more storage.

**Best Practices:**
- Use `ON DELETE CASCADE` only if profiles should never exist without users.
- Add `UNIQUE` constraints if profiles must be unique per user.

---

### **3.2 One-to-Many Relationships**
**When to Use:**
- Parent-to-child hierarchies (e.g., departments ↔ employees, authors ↔ books).
- Modeling composition or aggregation (e.g., orders ↔ order_items).

**Schema Example:**
```sql
CREATE TABLE departments (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE employees (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  department_id INT,
  FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

**Query Optimization:**
- **Index the Foreign Key**:
  ```sql
  CREATE INDEX idx_employees_department ON employees(department_id);
  ```
- **Use `LEFT JOIN`** to preserve parent rows with no children:
  ```sql
  SELECT d.name, e.name
  FROM departments d
  LEFT JOIN employees e ON d.id = e.department_id;
  ```

**Edge Cases:**
- **Cascading Deletes**: Use `ON DELETE CASCADE` for automatic cleanup.
- **Partial Deletes**: Use `ON DELETE SET NULL` if child rows should persist:
  ```sql
  ALTER TABLE employees
  DROP FOREIGN KEY employees_department_fk,
  ADD CONSTRAINT employees_department_fk
  FOREIGN KEY (department_id) REFERENCES departments(id)
  ON DELETE SET NULL;
  ```

---

### **3.3 Many-to-Many Relationships**
**When to Use:**
- Representing complex associations (e.g., users ↔ roles, students ↔ courses).
- Avoid over-normalization; denormalize if performance suffers.

**Schema Example:**
```sql
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE roles (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

-- Junction table with composite primary key
CREATE TABLE user_roles (
  user_id INT NOT NULL,
  role_id INT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

**Query Patterns:**
1. **Insert/Update/Delete Operations**:
   ```sql
   -- Assign role to user
   INSERT INTO user_roles (user_id, role_id) VALUES (1, 2);

   -- Revoke role from user
   DELETE FROM user_roles WHERE user_id = 1 AND role_id = 2;
   ```
2. **Querying Associations**:
   ```sql
   -- Find all users with a specific role
   SELECT u.name
   FROM users u
   JOIN user_roles ur ON u.id = ur.user_id
   JOIN roles r ON ur.role_id = r.id
   WHERE r.name = 'admin';
   ```

**Optimization:**
- **Add Indexes** to junction table columns:
  ```sql
  CREATE INDEX idx_user_roles_user ON user_roles(user_id);
  CREATE INDEX idx_user_roles_role ON user_roles(role_id);
  ```
- **Denormalize if Needed**: Cache role names in the junction table for faster reads.

**Alternatives:**
- **Self-Referential Tables**: For hierarchical M:N (e.g., social networks):
  ```sql
  CREATE TABLE friends (
    user_id INT REFERENCES users(id),
    friend_id INT REFERENCES users(id),
    PRIMARY KEY (user_id, friend_id)
  );
  ```

---

## **4. Query Examples**

### **4.1 One-to-One Queries**
**Retrieve a user’s profile:**
```sql
SELECT u.name, p.bio
FROM users u
JOIN user_profiles p ON u.id = p.id;
```

**Retrieve users without profiles:**
```sql
SELECT u.id, u.name
FROM users u
LEFT JOIN user_profiles p ON u.id = p.id
WHERE p.id IS NULL;
```

---

### **4.2 One-to-Many Queries**
**List all employees in a department:**
```sql
SELECT e.name, d.name AS department
FROM employees e
JOIN departments d ON e.department_id = d.id
WHERE d.name = 'Engineering';
```

**Count employees per department:**
```sql
SELECT d.name, COUNT(e.id) AS employee_count
FROM departments d
LEFT JOIN employees e ON d.id = e.department_id
GROUP BY d.name;
```

---

### **4.3 Many-to-Many Queries**
**List all roles for a user:**
```sql
SELECT r.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.id = 1;
```

**Check if a user has a role:**
```sql
SELECT EXISTS (
  SELECT 1
  FROM user_roles ur
  JOIN roles r ON ur.role_id = r.id
  WHERE ur.user_id = 1 AND r.name = 'admin'
) AS has_admin_role;
```

**Pivot Table (SQL Server):**
```sql
SELECT
  u.id,
  MAX(CASE WHEN r.name = 'admin' THEN 1 ELSE 0 END) AS is_admin,
  MAX(CASE WHEN r.name = 'editor' THEN 1 ELSE 0 END) AS is_editor
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
GROUP BY u.id;
```

---

## **5. Related Patterns**

| **Pattern**                  | **Description**                                                                 | **When to Use**                                                                                     |
|------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **[Single Table Inheritance](https://martinfowler.com/eaaCatalog/singleTableInheritance.html)** | Extend a parent table with child-specific columns (e.g., `employees` ↔ `managers`). | When child tables share >50% of columns; avoid for highly variable data.                          |
| **[Join Table Inheritance](https://martinfowler.com/eaaCatalog/joinTableInheritance.html)** | Store child types in a separate table with a type discriminator.               | For hierarchical data (e.g., `shapes` → `circle`, `square`).                                       |
| **[Composite Key](https://use-the-index-luke.com/no/foreign-keys/foreign-key)** | Use a composite key for junction tables instead of a surrogate key.                | In many-to-many relationships to reduce storage and improve query performance.                     |
| **[Denormalization](https://martinfowler.com/eaaCatalog/denormalizer.html)** | Strategically duplicate data to improve read performance.                         | When read-heavy queries outperform normalized joins (e.g., caching role names in `user_roles`).    |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Store state changes as a sequence of events instead of snapshots.                 | For audit trails or complex transaction histories (e.g., logging user role changes).               |
| **[Sharding](https://martinfowler.com/eaaCatalog/databaseSharding.html)**           | Split data across multiple databases/servers.                              | Horizontal scaling for large-scale applications (e.g., user data sharded by region).              |

---

## **6. Anti-Patterns to Avoid**
1. **Circular References**:
   - Avoid bidirectional 1:N relationships (e.g., `A → B` and `B → A` without a junction table).
   - *Fix*: Use a junction table for M:N; otherwise, denormalize one direction.

2. **Over-Normalization**:
   - Excessive joins can slow queries. Denormalize if:
     - A query frequently accesses unrelated data.
     - The cost of joins outweighs storage savings.

3. **Orphaned Foreign Keys**:
   - Never allow foreign keys to reference non-existent primary keys. Always use `ON DELETE CASCADE`, `SET NULL`, or triggers to enforce integrity.

4. **Self-Referential Without Constraints**:
   - In recursive relationships (e.g., `employees` referencing their `manager_id`), add a constraint to prevent cycles:
     ```sql
     ALTER TABLE employees
     ADD CONSTRAINT no_self_references CHECK (manager_id != id);
     ```

5. **Ignoring Indexes**:
   - Foreign keys and frequently queried columns should always be indexed. Use `EXPLAIN ANALYZE` to identify slow queries.

---
## **7. Tools & Extensions**
- **Database Design**:
  - [Lucidchart](https://www.lucidchart.com/) (visual diagrams).
  - [dbdiagram.io](https://dbdiagram.io/) (markdown-based schemas).
- **ORM Tools**:
  - **ActiveRecord** (Rails), **Entity Framework** (C#), **SQLAlchemy** (Python) automatically generate relationship mappings.
- **Query Analyzers**:
  - **pgAdmin** (PostgreSQL), **MySQL Workbench**, **SQL Server Management Studio** for execution plans.

---
## **8. Further Reading**
- [Database Normalization (Wikipedia)](https://en.wikipedia.org/wiki/Database_normalization)
- [Martin Fowler’s Patterns of Enterprise Application Architecture](https://martinfowler.com/eaaCatalog/)
- [Index Effectiveness](https://use-the-index-luke.com/) (for optimizing queries).
- [SQL Performance Explained](https://use-the-index-luke.com/) (by Markus Winand).