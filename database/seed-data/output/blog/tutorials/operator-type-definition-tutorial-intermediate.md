```markdown
# **Operator Type Definition (OTD): The Clean Way to Handle Query Operators in APIs**

*How to elegantly define, reuse, and validate comparison operators across your database and API layers—without duplicating logic everywhere.*

---

## **Introduction**

Have you ever looked at your application’s query parameters and thought, *"This is getting messy"*?

Consider an API endpoint that accepts filtering for user records:

```json
GET /api/users?name[eq]=John&age[gt]=25&status[in]=active,pending
```

At first glance, it seems clean—but under the hood, your backend likely has a sprawling switch statement or series of `if` checks to handle operators like `eq`, `ne`, `lt`, `gt`, `in`, and `like`. Managing these operators manually is error-prone, especially as your API grows.

The **Operator Type Definition** pattern solves this by centralizing operator logic into a reusable component. Instead of scattering `eq`, `gt`, and `like` logic across controllers, services, and database adapters, you define them once and apply them consistently.

This pattern isn’t just about reducing boilerplate—it enforces consistency, improves maintainability, and makes APIs more predictable. In this post, we’ll explore:
- Why manually handling operators creates headaches
- How OTD centralizes and standardizes operator logic
- Practical implementations in JavaScript (Node.js), Python (Django), and SQL
- Common pitfalls and how to avoid them

---

## **The Problem: Query Operators Without OTD**

Without a structured approach to operators, your system faces these challenges:

### 1. **Duplicated Logic Everywhere**
Each layer (API, service, repository) may implement its own operator handling, leading to inconsistencies. For example:
- Your API might accept `name[eq]=John`, but the database adapter ignores it because it expects `name = 'John'` instead.
- Your frontend may use `status[ne]=inactive`, but the backend treats it as a strict equality check.

### 2. **Error-Prone Parsing**
Hardcoding operator strings (e.g., `eq`, `ne`) in string comparisons is fragile. A typo in the operator string could break queries silently.

### 3. **No Validation**
Without validation, malformed operator usage (e.g., `age[ne]` without a value) might slip through and cause runtime errors.

### 4. **Database-Specific Quirks**
Different databases handle operators like `IN`, `LIKE`, and `BETWEEN` differently. Mixing operator logic with database drivers complicates refactoring.

### 5. **Scalability Nightmares**
As your API adds new operators (e.g., `between`, `contains`) or fields, you must update every layer manually. This creates technical debt.

---

## **The Solution: Operator Type Definition**

The **Operator Type Definition (OTD)** pattern solves these problems by:
- **Centralizing operator definitions** (e.g., `eq`, `gt`, `in`) in a single, reusable component.
- **Standardizing parsing and validation** to ensure consistent behavior across layers.
- **Decoupling operators from database logic**, making it easier to switch databases or add new ones.

### **Core Components**
1. **Operator Registry**: A map of operator names to their implementations (e.g., `eq: (field, value) => field === value`).
2. **Parser**: Converts raw input (e.g., `name[eq]=John`) into structured objects (e.g., `{ field: "name", operator: "eq", value: "John" }`).
3. **Validator**: Ensures operators are used correctly (e.g., `IN` requires an array).
4. **Query Builder**: Translates structured operators into database-agnostic queries.

---

## **Implementation Guide**

We’ll implement OTD in three layers:
1. **API Layer**: Parse and validate operators from raw input.
2. **Service Layer**: Apply operators to business logic.
3. **Repository Layer**: Translate operators into database queries.

---

### **1. JavaScript (Node.js) Example**
#### **Operator Registry**
Define operators as functions that return comparison logic:
```javascript
const operators = {
  eq: (field, value) => ({ [field]: value }),
  ne: (field, value) => ({ [field]: { [Symbol.for('ne')]: value } }),
  gt: (field, value) => ({ [field]: { $gt: value } }),
  lt: (field, value) => ({ [field]: { $lt: value } }),
  in: (field, values) => ({ [field]: { $in: values } }),
  like: (field, pattern) => ({ [field]: { $regex: new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) } }),
};

export default operators;
```

#### **Parser**
Convert `name[eq]=John` to `{ field: "name", operator: "eq", value: "John" }`:
```javascript
function parseOperators(queryParams) {
  const operators = {};
  for (const [key, value] of Object.entries(queryParams)) {
    if (key.includes('[') && key.includes(']')) {
      const [field, opAndValue] = key.split('[').map(part => part.split(']')[0]);
      const [op, rawValue] = opAndValue.split('=');
      const value = decodeURIComponent(rawValue || '');
      operators[field] = { operator: op, value };
    }
  }
  return operators;
}
```

#### **Validator**
Ensure operators are valid and values are correct:
```javascript
function validateOperators(operators) {
  for (const [field, { operator, value }] of Object.entries(operators)) {
    if (!operators[operator]) {
      throw new Error(`Invalid operator: ${operator}`);
    }
    if (operator === 'in' && !Array.isArray(value)) {
      throw new Error(`Operator 'in' requires an array`);
    }
  }
}
```

#### **Query Builder**
Convert structured operators to MongoDB-style queries:
```javascript
function buildQuery(operators) {
  const query = {};
  for (const [field, { operator, value }] of Object.entries(operators)) {
    query[...operators[field](field, value)];
  }
  return query;
}
```

#### **Usage**
```javascript
const queryParams = {
  'name[eq]': 'John',
  'age[gt]': '25',
  'status[in]': 'active,pending'
};

const parsed = parseOperators(queryParams);
validateOperators(parsed);
const query = buildQuery(parsed);

console.log(query);
// Output: { name: 'John', age: { $gt: 25 }, status: { $in: ['active', 'pending'] } }
```

---

### **2. Python (Django ORM) Example**
#### **Operator Registry**
```python
from django.db.models import Q

OPERATORS = {
    'eq': lambda field, value: Q(**{f'{field}__exact': value}),
    'ne': lambda field, value: Q(**{f'{field}__iexact': value}),
    'gt': lambda field, value: Q(**{f'{field}__gt': value}),
    'lt': lambda field, value: Q(**{f'{field}__lt': value}),
    'in': lambda field, value: Q(**{f'{field}__in': value}),
    'like': lambda field, value: Q(**{f'{field}__icontains': value}),
}
```

#### **Parser**
```python
import re

def parse_operators(query_string):
    operators = {}
    for match in re.finditer(r'(\w+)\[([^\]]+)\]=(.*)', query_string):
        field, op, value = match.groups()
        operators[field] = {'operator': op, 'value': value}
    return operators
```

#### **Validator**
```python
def validate_operators(operators):
    for field, data in operators.items():
        if data['operator'] not in OPERATORS:
            raise ValueError(f"Invalid operator: {data['operator']}")
```

#### **Query Builder**
```python
def build_query(operators):
    q = Q()
    for field, data in operators.items():
        operator_func = OPERATORS[data['operator']]
        q &= operator_func(field, data['value'])
    return q
```

#### **Usage**
```python
query_string = 'name[eq]=John&age[gt]=25&status[in]=active,pending'
parsed = parse_operators(query_string)
validate_operators(parsed)
query = build_query(parsed)

User.objects.filter(query)
```

---

### **3. SQL Query Builder (PostgreSQL Example)**
#### **Operator Registry**
```sql
-- Define a mapping of operators to SQL syntax
CREATE TABLE operator_definitions (
    operator_name VARCHAR(10) PRIMARY KEY,
    sql_pattern   TEXT NOT NULL,
    example       TEXT
);

INSERT INTO operator_definitions VALUES
('eq', 'column = %s', 'name = "John"'),
('ne', 'column != %s', 'name != "John"'),
('gt', 'column > %s', 'age > 25'),
('lt', 'column < %s', 'age < 25'),
('in', 'column IN (%s)', 'status IN ("active", "pending")'),
('like', 'column LIKE %s', 'name LIKE "%ohn%"');
```

#### **Parser**
```javascript
// JavaScript example (similar to above)
function sqlizeOperators(operators) {
  const sqlFragments = [];
  const params = [];
  for (const [field, { operator, value }] of Object.entries(operators)) {
    const opDef = OPERATOR_DEFS[operator];
    const fragment = opDef.sql_pattern.replace('%s', `?`);
    sqlFragments.push(`${field} ${fragment}`);
    params.push(value);
  }
  return { sql: sqlFragments.join(' AND '), params };
}
```

#### **Usage**
```javascript
const opDefs = { /* ... */ }; // Populated from operator_definitions table
const { sql, params } = sqlizeOperators(parsedOperators);

const query = `SELECT * FROM users WHERE ${sql}`;
const result = db.query(query, params);
```

---

## **Common Mistakes to Avoid**

1. **Assuming All Operators Are Supported by the Database**
   - Not all databases support `$in` or `$regex` operators. Always validate against your database’s capabilities.

2. **Ignoring Validation**
   - Always validate operator usage (e.g., ensure `IN` has an array). Without validation, users can craft invalid queries.

3. **Hardcoding SQL Patterns**
   - If you hardcode SQL patterns (e.g., `column = %s`), you risk SQL injection. Use parameterized queries.

4. **Overcomplicating the Parser**
   - Start simple (e.g., `name[eq]=John`) before adding complex features like nested operators.

5. **Not Testing Edge Cases**
   - Test operators with:
     - Missing values (`name[eq]` → error)
     - Invalid operators (`name[xyz]=John` → error)
     - Special characters in values (`name[like]='John%'`)

6. **Coupling Operators to a Specific Database**
   - Design your OTD to be database-agnostic. Abstract the query building layer to support multiple databases.

7. **Forgetting to Document Operators**
   - Document supported operators in your API docs (e.g., Swagger/OpenAPI). Users rely on this.

---

## **Key Takeaways**

- **Operator Type Definition centralizes operator logic**, reducing duplication and inconsistencies.
- **Standardize parsing and validation** to catch errors early.
- **Decouple operators from databases** for flexibility.
- **Start simple** but design for extensibility (e.g., add `between`, `contains` later).
- **Validate thoroughly** to prevent runtime errors.
- **Document operators** in your API specs for clarity.

---

## **Conclusion**

The Operator Type Definition pattern is a straightforward yet powerful way to manage query operators in APIs. By centralizing operator logic, validating input early, and keeping database concerns separate, you build more maintainable, scalable, and predictable systems.

### **Next Steps**
1. **Adopt OTD for your next API endpoint**—start small and iterate.
2. **Experiment with database-agnostic query builders** (e.g., Knex.js for SQL, Mongoose for MongoDB).
3. **Extend the pattern** to support custom operators (e.g., `fulltext`, `jsonb_contains`).
4. **Share your implementation**—contribute to open-source libraries or discuss tradeoffs with peers.

Operators don’t have to be a messy afterthought. With OTD, you can treat them like first-class citizens—consistent, validated, and reusable.

---

**What’s your experience with query operators? Have you encountered similar challenges? Share your thoughts in the comments!**
```