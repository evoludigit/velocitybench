---
# **[Pattern] Recursive CTEs for Hierarchical Data – Reference Guide**
*Query hierarchical relationships efficiently in SQL using recursive Common Table Expressions (CTEs).*

---

## **1. Overview**
Recursive CTEs (also called **Hierarchical Recursive CTEs**) allow you to traverse multi-level hierarchical data in SQL without self-joins or application-side recursion. This pattern is ideal for:
- **Organizational charts** (employee-department trees)
- **Product category trees** (e-commerce)
- **File system navigation** (folder hierarchies)
- **Comment threads** (discussion forums)
- **Bill of materials** (engineering assemblies)

A recursive CTE consists of:
1. **Anchor member**: The base query that defines the starting node(s).
2. **Recursive member**: A query that references the CTE itself to fetch child nodes.
3. **UNION ALL**: Combines the anchor and recursive results into a single result set.

By defining a traversal rule (e.g., `WHERE parent_id = current_id`), the CTE recursively expands to include all levels of the hierarchy.

---

## **2. Schema Reference**
Assume the following table structure for demonstration:

| **Column**      | **Type**       | **Description**                          |
|-----------------|----------------|------------------------------------------|
| `id`            | `INT` (PK)     | Unique identifier for the node.          |
| `name`          | `VARCHAR(255)` | Name/label of the node (e.g., department). |
| `parent_id`     | `INT` (FK)     | ID of the parent node (NULL for root).   |
| `depth`         | `INT` (optional) | Hierarchy level (0 for root, 1 for children). |

**Sample Data**:
```sql
INSERT INTO nodes (id, name, parent_id, depth)
VALUES
    (1, 'Executive', NULL, 0),        -- Root node
    (2, 'Engineering', 1, 1),
    (3, 'Marketing', 1, 1),
    (4, 'Research', 2, 2),
    (5, 'Development', 2, 2),
    (6, 'Sales', 3, 2);
```

---

## **3. Query Examples**
### **3.1 Basic Recursive Query (All Descendants)**
Retrieve a subtree starting from a given node (e.g., `id = 2` for "Engineering"):

```sql
WITH RECURSIVE node_hierarchy AS (
    -- Anchor: Start with the root node(s)
    SELECT
        id,
        name,
        parent_id,
        depth,
        CAST(id AS VARCHAR) AS path  -- Track traversal path
    FROM nodes
    WHERE id = 2  -- Start with "Engineering"

    UNION ALL

    -- Recursive: Join to find child nodes
    SELECT
        n.id,
        n.name,
        n.parent_id,
        nh.depth + 1,
        nh.path || '>' || CAST(n.id AS VARCHAR)
    FROM nodes n
    JOIN node_hierarchy nh ON n.parent_id = nh.id
)
SELECT * FROM node_hierarchy ORDER BY depth, name;
```
**Output**:
```
id | name       | parent_id | depth | path
---|------------|-----------|-------|---------------------
2  | Engineering| 1         | 0     | 2
4  | Research   | 2         | 1     | 2>4
5  | Development| 2         | 1     | 2>5
```

---

### **3.2 Query with Constraints (Depth Limit)**
Limit recursion to 2 levels (exclude grandchildren):

```sql
WITH RECURSIVE constrained_hierarchy AS (
    SELECT
        id, name, parent_id, depth, CAST(id AS VARCHAR) AS path
    FROM nodes
    WHERE id = 2

    UNION ALL

    SELECT
        n.id, n.name, n.parent_id, ch.depth + 1, ch.path || '>' || CAST(n.id AS VARCHAR)
    FROM nodes n
    JOIN constrained_hierarchy ch ON n.parent_id = ch.id
    WHERE ch.depth < 2  -- Stop at depth 1
)
SELECT * FROM constrained_hierarchy ORDER BY depth, name;
```

---

### **3.3 Path-Building for Navigation**
Generate hierarchical paths (e.g., for breadcrumbs):

```sql
WITH RECURSIVE path_builder AS (
    SELECT
        id,
        name,
        parent_id,
        depth,
        CAST(id AS VARCHAR) AS full_path
    FROM nodes
    WHERE id = 2

    UNION ALL

    SELECT
        n.id,
        n.name,
        n.parent_id,
        pb.depth + 1,
        pb.full_path || ' > ' || n.name
    FROM nodes n
    JOIN path_builder pb ON n.parent_id = pb.id
)
SELECT full_path AS hierarchical_path FROM path_builder;
```
**Output**:
```
hierarchical_path
-----------------------
2 > Engineering
2 > Engineering > Research
2 > Engineering > Development
```

---

### **3.4 Querying Ancestors (Reverse Traversal)**
Find all ancestors of a node (requires a self-referencing table):

```sql
WITH RECURSIVE ancestor_query AS (
    -- Anchor: Start with the target node
    SELECT id, name, parent_id, depth
    FROM nodes
    WHERE id = 4  -- Start with "Research"

    UNION ALL

    -- Recursive: Move up the tree
    SELECT
        n.id, n.name, n.parent_id, aq.depth + 1
    FROM nodes n
    JOIN ancestor_query aq ON n.id = aq.parent_id
    WHERE n.id IS NOT NULL
)
SELECT * FROM ancestor_query ORDER BY depth;
```
**Output**:
```
id | name       | parent_id | depth
---|------------|-----------|-------
4  | Research   | 2         | 0
2  | Engineering| 1         | 1
1  | Executive  | NULL      | 2
```

---
### **3.5 Multiple Starting Points**
Query all roots and their descendants:

```sql
WITH RECURSIVE all_hierarchies AS (
    -- Anchor: All root nodes (parent_id IS NULL)
    SELECT
        id, name, parent_id, depth, CAST(id AS VARCHAR) AS path
    FROM nodes
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive: Join to children
    SELECT
        n.id, n.name, n.parent_id, ah.depth + 1, ah.path || '>' || CAST(n.id AS VARCHAR)
    FROM nodes n
    JOIN all_hierarchies ah ON n.parent_id = ah.id
)
SELECT * FROM all_hierarchies ORDER BY path;
```

---

## **4. Key Considerations**
### **4.1 Performance Optimizations**
- **Indexing**: Ensure `parent_id` and `id` are indexed.
- **Depth Limiting**: Use `WHERE depth < N` to avoid infinite loops or deep recursion.
- **Materialized Paths**: For large hierarchies, consider storing paths as strings (e.g., `path_column`) instead of recursive queries.
- **Database Limits**: Check your DBMS’ recursion depth limit (e.g., PostgreSQL allows default 1000 levels).

### **4.2 Handling Cycles**
Recursive CTEs will fail on cyclic references (e.g., `A -> B -> A`). Validate data integrity or use application logic to prevent cycles.

### **4.3 Database-Specific Syntax**
- **PostgreSQL**: Uses `WITH RECURSIVE`.
- **SQL Server**: Uses `WITH` without `RECURSIVE`.
- **Oracle**: Supports recursive CTEs in 10g+.
- **MySQL**: Limited support (8.0+ with `RECURSIVE` keyword).

---
## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Use Case**                          |
|----------------------------------|---------------------------------------------------------------------------------|----------------------------------------|
| **[Materialized Path](link)**   | Store paths as strings (e.g., `1>2>4` for "Research") to avoid recursion.      | Read-heavy hierarchies.               |
| **[Adjacency List](link)**      | Standard parent-child relationship (default in this guide).                   | Simple hierarchies with no cycles.    |
| **[Nested Set](link)**          | Uses `left`/`right` values for fast ancestor lookups.                          | Complex hierarchies with frequent lookups. |
| **[Closure Table](link)**       | Pre-computes all ancestor-descendant relationships in a table.                 | High-write hierarchies.               |
| **[Graph Algorithms](link)**    | Traverse graphs using recursive CTEs with custom traversal rules.              | Network/topology data.                 |

---
## **6. Common Pitfalls**
1. **Infinite Recursion**:
   - **Cause**: Missing `WHERE` condition in the recursive member (e.g., `WHERE parent_id = id`).
   - **Fix**: Add a termination condition (e.g., `WHERE depth < N`).

2. **Missing Anchor**:
   - **Cause**: Forgetting to include the base case.
   - **Fix**: Always define the anchor member first.

3. **Performance Degradation**:
   - **Cause**: Unindexed columns or deep recursion.
   - **Fix**: Optimize queries with indexing and depth limits.

4. **Database Compatibility**:
   - **Cause**: Syntax errors in non-recursive CTE-supporting DBs.
   - **Fix**: Test queries on your target database.

---
## **7. When to Avoid Recursive CTEs**
- **Static Hierarchies**: If the data is rarely updated, use a **materialized path** or **nested set** for faster reads.
- **Extremely Deep Trees**: For >1000 levels, consider alternative patterns (e.g., closure table).
- **Non-SQL Clients**: If your application logic handles hierarchies, avoid SQL recursion for simplicity.

---
## **8. Full Example: Department Hierarchy with Paths**
```sql
WITH RECURSIVE department_tree AS (
    -- Anchor: Start with root departments
    SELECT
        id,
        name,
        parent_id,
        0 AS depth,
        CAST(id AS VARCHAR) AS path
    FROM departments
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive: Add child departments
    SELECT
        d.id,
        d.name,
        d.parent_id,
        dt.depth + 1,
        dt.path || ' > ' || d.name
    FROM departments d
    JOIN department_tree dt ON d.parent_id = dt.id
)
SELECT
    id,
    name AS department,
    depth,
    path AS hierarchical_path
FROM department_tree
ORDER BY path;
```