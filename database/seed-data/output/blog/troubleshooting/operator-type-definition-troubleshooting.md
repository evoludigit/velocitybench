# **Debugging Operator Type Definition Patterns: A Troubleshooting Guide**
*QuicklyResolve Issues with `eq`, `ne`, `lt`, `gt`, `in`, and `like`*

This guide focuses on debugging **Operator Type Definition (OTD) patterns**, particularly `eq` (equal), `ne` (not equal), `lt` (less than), `gt` (greater than), `in`, and `like` operators. These are commonly used in query logic, filtering, and dynamic rule engines.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common signs of operator pattern issues:

| Symptom                          | Likely Cause                          |
|----------------------------------|---------------------------------------|
| Queries return **wrong results** | Incorrect operator usage or data type mismatch |
| Performance **degradation**       | Overly complex `in`/`like` conditions |
| Type errors (`TypeError`, `InvalidCast`) | Wrong data types in comparisons (e.g., comparing a string to a number) |
| Unexpected `NULL` behavior       | Missing `IS NULL`/`IS NOT NULL` logic |
| Rules failing in **edge cases**  | Neglected null checks or boundary conditions |
| **Stack traces** pointing to operator logic | Debugging required in rule engine/API layer |

---

## **2. Common Issues and Fixes (with Code Examples)**

### **2.1. Data Type Mismatch**
**Symptom:**
`"Cannot compare string to integer"`
**Cause:** Operators always enforce strict type checking unless explicitly handled.

**Fix:**
- **Explicitly cast values** before comparison:
  ```python
  # Bad: Direct comparison
  if age == "30"  # TypeError if age is an integer
      pass

  # Good: Cast to common type
  if age == int("30"):  # Works if age is an int
      pass

  # Best: Use type-agnostic comparison (if allowed)
  if str(age) == "30":
      pass
  ```
- **Use dynamic typing carefully** (e.g., SQL `CAST` or database-specific functions).

---

### **2.2. NULL Handling in `eq`, `ne`**
**Symptom:**
`"NULL value encountered when comparing"`
**Cause:** Direct comparisons with `NULL` always return `NULL` (not `True`/`False`).

**Fix:**
- **Replace `eq`/`ne` with `IS NULL`/`IS NOT NULL`**:
  ```python
  # Bad: Fails with NULL (returns NULL)
  if user_status == None:
      pass

  # Good: Explicit NULL checks
  if pd.isna(user_status):  # For Pandas
      pass
  if user_status is None:     # Python
      pass
  ```
- **Database SQL Example**:
  ```sql
  -- Bad: Returns NULL if user_status is NULL
  SELECT * FROM users WHERE user_status = 'active';

  -- Good: Explicit NULL check
  SELECT * FROM users WHERE (user_status = 'active' OR user_status IS NULL);
  ```

---

### **2.3. Inefficient `in` Clauses**
**Symptom:**
`"Query timeout" or slow performance`
**Cause:** Large `in` lists (>1000 items) can bloat queries.

**Fix:**
- **Use `EXISTS` for large lists** (reduces memory usage):
  ```sql
  -- Bad: Long IN clause
  SELECT * FROM products WHERE id IN (1, 2, ..., 1000);

  -- Good: Batch query with EXISTS
  SELECT * FROM products
  WHERE EXISTS (SELECT 1 FROM ids WHERE product_id = p.id);
  ```
- **For Python/Pandas**:
  ```python
  # Bad: Large lookup
  if x in large_list:
      pass

  # Good: Use sets for O(1) lookups
  lookup_set = set(large_list)  # Faster for membership tests
  ```

---

### **2.4. `like` Operator Issues**
**Symptom:**
`"%abc%" doesn't match expected patterns`
**Cause:** SQL `LIKE` is case-sensitive unless configured otherwise.

**Fix:**
- **Use case-insensitive matching**:
  ```sql
  -- For PostgreSQL/MySQL (case-insensitive)
  SELECT * FROM users WHERE LOWER(name) LIKE '%abc%';

  -- For SQL Server (collation handling)
  SELECT * FROM users WHERE name COLLATE SQL_Latin1_General_CP1_CS_AS LIKE '%abc%';
  ```
- **Python Regex Alternative**:
  ```python
  import re
  matches = re.findall(r'abc', 'Some text here', re.IGNORECASE)
  ```
- **Fix wildcards**:
  - `%` = 0 or more characters
  - `_` = single character
  - Avoid leading `%` in keys (performance hit).

---

### **2.5. Boundary Conditions in `lt`/`gt`**
**Symptom:**
`"Out-of-bounds errors" or missed edge cases`
**Cause:** Including/excluding boundaries (`<`, `>`, `<=`, `>=`).

**Fix:**
- **Clarify requirements**:
  ```python
  # Does age 20 qualify if max_age = 20?
  if age <= max_age:  # Includes 20
      pass
  if age < max_age:   # Excludes 20
      pass
  ```
- **Test with extreme values** (e.g., `MIN`, `MAX`, `NULL`).

---

### **2.6. Dynamic Operator Handling**
**Symptom:**
`"Operator not supported" errors`
**Cause:** Dynamically setting operators (e.g., from user input).

**Fix:**
- **Whitelist allowed operators**:
  ```python
  ALLOWED_OPERATORS = {'eq', 'ne', 'gt', 'lt', 'in', 'like'}
  operator = user_input  # Sanitize!
  if operator not in ALLOWED_OPERATORS:
      raise ValueError("Invalid operator")
  ```
- **For SQL generation**:
  ```python
  if operator == 'eq':
      sql = f"{column} = '{value}'"
  elif operator == 'like':
      sql = f"{column} LIKE '%{value}%'"
  # Always escape SQL to prevent injection!
  ```

---

## **3. Debugging Tools and Techniques**

### **3.1. Logging and Validation**
- **Log operator inputs** for transparency:
  ```python
  logging.info(f"Applying operator {op} with args {args}")
  ```
- **Validate data types before comparisons**:
  ```python
  assert isinstance(age, int), "Age must be an integer"
  ```

### **3.2. Unit Testing**
- **Test edge cases** for each operator:
  ```python
  # Test NULL behavior
  assert (None == None) is False  # NULL != NULL in SQL
  assert pd.isna(None) is True   # Use isna() for NULL checks
  ```
- **Use test frameworks** (e.g., `pytest`, `JUnit`) to automate checks.

### **3.3. Database Profiling**
- **Slow query analysis**:
  ```sql
  -- PostgreSQL: Check query plan
  EXPLAIN ANALYZE SELECT * FROM users WHERE name LIKE '%abc%';
  ```
- **Index suggestions**:
  - Add indexes for `LIKE`/`IN` columns if queries are slow.

### **3.4. Code Inspection**
- **Static analysis tools** (e.g., `pylint`, `sonarqube`) to catch:
  - Unsafe type comparisons.
  - SQL injection risks.

---

## **4. Prevention Strategies**

### **4.1. Type Safety**
- **Use type hints** (Python):
  ```python
  def compare_numbers(a: int, b: str) -> bool:
      return int(a) == int(b)  # Explicit conversion
  ```
- **Database fields**: Declare strict types (e.g., `INTEGER` instead of `TEXT`).

### **4.2. Operator Whitelisting**
- **Never trust user-provided operators** (SQL injection risk).
- **Use ORM-safe methods** (e.g., Django’s `Q` objects, SQLAlchemy filters).

### **4.3. Documentation**
- **Document operator behavior**:
  ```markdown
  ## Operator Behavior
  - `eq`: Strict equality (NULL returns NULL)
  - `in`: Case-sensitive unless collation specifies otherwise
  ```
- **Include examples** for `like` wildcards.

### **4.4. Performance Tuning**
- **Limit `IN` clause size** (e.g., batch queries).
- **Use `LIMIT` in rule engines** to cap result sets.

### **4.5. Monitoring**
- **Track slow operator usage** (e.g., `like` with wildcards at start).
- **Alert on NULL-heavy comparisons**.

---

## **5. Summary Checklist for Quick Fixes**
| Issue                | Quick Fix                          | Tools/Examples                          |
|----------------------|-------------------------------------|-----------------------------------------|
| Type mismatch        | Explicit casting                    | `int(x)`, `str(y)`                      |
| NULL in `eq`/`ne`    | Use `IS NULL/IS NOT NULL`           | `pd.isna()`, `is None`                  |
| Large `IN` clauses   | Use `EXISTS` or batch queries       | SQL `EXISTS`, Python `set()` lookups   |
| Case-sensitive `like`| Use `LOWER()` or regex              | `LOWER(name) LIKE '%abc%'`             |
| Dynamic operators    | Whitelist operators                 | `ALLOWED_OPERATORS = {'eq', 'gt'}`     |
| Performance issues   | Index columns, limit results        | `EXPLAIN ANALYZE`, `LIMIT 1000`         |

---
**Final Tip:** Start by **logging operator inputs/outputs**—90% of debugging involves tracing the data flow.

---
This guide ensures you **quickly identify, replicate, and resolve** common `OTD` pattern issues. Adjust based on your language/database stack.