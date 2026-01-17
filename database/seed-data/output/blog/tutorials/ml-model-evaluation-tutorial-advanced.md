```markdown
---
title: "Model Evaluation Patterns: How to Handle Dynamic Business Logic in Databases"
date: YYYY-MM-DD
author: "Jane Doe"
description: "Learn how to implement robust model evaluation patterns in your backend systems to handle dynamic business rules without bloating your application code."
tags: ["database", "api", "backend", "patterns", "sql"]
---

# **Model Evaluation Patterns: How to Handle Dynamic Business Logic in Databases**

As backend engineers, we often find ourselves in a delicate balance: we want to keep business logic as close to the data as possible (for performance and consistency), but we also need to avoid drowning our database schema in overly complex rules. This is where **Model Evaluation Patterns** come into play—a set of techniques to encapsulate, evaluate, and enforce business rules in a maintainable way.

In this post, we’ll explore why traditional approaches fall short, how to structure evaluation logic effectively, and practical ways to implement these patterns in your stack. You’ll leave with actionable patterns you can apply to your next project.

---

## **The Problem: Static Schemas vs. Dynamic Business Logic**

Databases are fantastic for storing data and enforcing *static* constraints (e.g., `NOT NULL`, `UNIQUE`, or foreign keys). However, many business rules are **dynamic**—they change due to promotions, seasonality, or user-specific preferences. Storing these rules in application code leads to:

- **Tight coupling** between your DB schema and business logic.
- **Performance bottlenecks** when rules require cross-table lookups.
- **Scalability issues** as rules become harder to maintain in a monolithic app.

For example, imagine an e-commerce platform where discounts stack based on:
- The customer’s loyalty tier,
- The product category,
- The current month,
- A one-time flash sale.

If you hardcode this in your backend, you’ll face:
- **Spaghetti code** that’s hard to debug.
- **Slow queries** as rules are evaluated in application loops.
- **Versioning headaches** when rules change (e.g., “Why is December’s logic only in `v2.4.0`?”).

---

## **The Solution: Model Evaluation Patterns**

Model Evaluation Patterns are techniques to **externalize** business rules from application logic, making them:
- **Database-friendly** (where applicable).
- **Query-first** (minimizing round trips).
- **Easy to audit and modify** without redeploying apps.

The core idea? **Move rule evaluation into the DB or into a dedicated evaluation layer** that can be queried like data.

Here’s how we’ll approach it:

1. **Rule Tables**: Store rules as structured data (e.g., JSON or key-value pairs).
2. **Dynamic Query Generation**: Use a query builder or templating system to construct rules at runtime.
3. **Materialized Rules**: Precompute rule evaluations for performance-critical paths.
4. **Hybrid Approach**: Combine DB- and app-hosted rules for flexibility.

---

## **Components/Solutions: The Toolkit**

### **1. Rule Tables: Storing Business Logic as Data**
Instead of embedding rules in SQL or code, store them as records. For example:

```sql
-- Example: Discount rules table
CREATE TABLE discount_rules (
  rule_id SERIAL PRIMARY KEY,
  rule_name VARCHAR(255) NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  apply_to_product_category VARCHAR(50), -- e.g., "electronics", "NULL" for all
  discount_value NUMERIC(10, 2) NOT NULL,  -- e.g., 15.00
  customer_loyalty_tier INT,               -- NULL for all tiers
  month_active INT CHECK (month_active BETWEEN 1 AND 12),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Pros**:
- Rules can be updated without app changes.
- Easy to query which rules apply to a given scenario.

**Cons**:
- Requires a query layer to match rules to records.

---

### **2. Dynamic Query Generation**
Use a templating system or codegen to generate queries based on rules. Example in PostgreSQL with `jsonb`:

```sql
-- A function that dynamically evaluates rules for a given product
CREATE OR REPLACE FUNCTION evaluate_discounts(
  product_id INT,
  customer_loyalty_tier INT,
  current_month INT,
  category VARCHAR(50)
) RETURNS NUMERIC AS $$
DECLARE
  discount NUMERIC := 0;
  rule_record RECORD;
BEGIN
  FOR rule_record IN
    SELECT *
    FROM discount_rules
    WHERE
      (apply_to_product_category IS NULL OR apply_to_product_category = category)
      AND (customer_loyalty_tier IS NULL OR customer_loyalty_tier = (SELECT loyalty_tier FROM customers WHERE id = customer_id))
      AND (month_active IS NULL OR month_active = current_month)
      AND active = TRUE
  LOOP
    discount := discount + rule_record.discount_value;
  END LOOP;
  RETURN discount;
END;
$$ LANGUAGE plpgsql;
```

**Pros**:
- Rules are evaluated in the DB, reducing app load.
- Easy to extend with new rule types.

**Cons**:
- Performance may degrade with complex rules.

---

### **3. Materialized Rules (Precompute for Speed)**
For high-traffic scenarios, cache rule evaluations. Example with a materialized view:

```sql
CREATE MATERIALIZED VIEW product_discounts AS
SELECT
  p.id AS product_id,
  p.category,
  dr.discount_value,
  c.loyalty_tier,
  EXTRACT(MONTH FROM NOW()) AS current_month
FROM products p
JOIN discount_rules dr ON
  (dr.apply_to_product_category IS NULL OR dr.apply_to_product_category = p.category)
JOIN customers c ON
  (dr.customer_loyalty_tier IS NULL OR dr.customer_loyalty_tier = c.loyalty_tier)
WHERE dr.active = TRUE;
```

**Pros**:
- Near-instant lookups for common cases.
- Reduces query complexity.

**Cons**:
- Data becomes stale unless refreshed frequently.

---

### **4. Hybrid Approach: DB + App Logic**
For flexibility, use a **rule engine** (like Drools or a custom service) to evaluate rules in the app. Example with a Python service:

```python
# pseudo-code
class DiscountRuleEngine:
    def __init__(self, db_conn):
        self.db = db_conn

    def evaluate(self, product, customer):
        rules = self.db.query("""
            SELECT * FROM discount_rules
            WHERE
              (apply_to_product_category IS NULL OR apply_to_product_category = %s)
              AND (customer_loyalty_tier IS NULL OR customer_loyalty_tier = %s)
              AND month_active = EXTRACT(MONTH FROM NOW())
        """, (product.category, customer.loyalty_tier))

        discount = sum(r.discount_value for r in rules)
        return discount
```

**Pros**:
- More flexible than pure DB rules.
- Easier to unit test.

**Cons**:
- Adds latency if rules are complex.

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Identify Rules That Need Externalization**
Ask:
- Are these rules likely to change frequently?
- Do they affect many tables or require complex joins?
- Are they user-specific or time-sensitive?

### **Step 2: Choose a Strategy**
| Strategy               | Best For                          | Complexity |
|------------------------|-----------------------------------|------------|
| Rule tables            | Simple, infrequently changing rules| Low        |
| Dynamic queries        | Medium complexity rules           | Medium     |
| Materialized views     | High-read, low-change scenarios   | High       |
| Hybrid (app + DB)      | Dynamic, user-specific rules      | Medium     |

### **Step 3: Design Your Rule Storage**
- Use **JSONB** or **key-value columns** for flexible rules.
- Add an `active` flag to soft-delete rules.

### **Step 4: Implement Evaluation**
- Start with a **simple function** (like the PostgreSQL example).
- Optimize with **indexes** on frequently queried columns (e.g., `apply_to_product_category`).
- Cache results if needed.

### **Step 5: Test Thoroughly**
- Test edge cases (e.g., overlapping rules, inactive rules).
- Benchmark performance vs. the old approach.

---

## **Common Mistakes to Avoid**

### **1. Over-Complicating Rules Too Early**
- Don’t jump to a full rule engine if your rules are simple. Start with rule tables.
- Example: **Bad**: Using Drools for a 3-line discount.
- Example: **Good**: Start with a `discount_rules` table.

### **2. Ignoring Performance**
- Rule tables can bloat queries. Use **partial indexes** or **CTEs** for complex joins.
- Bad: `SELECT * FROM discount_rules WHERE ...` (scans thousands of rows).
- Good: `SELECT * FROM discount_rules WHERE customer_tier = 5 AND category = 'electronics'`.

### **3. Not Versioning Rules**
- Rules should have a `version` or `created_at` column so you can track changes.
- Example:
  ```sql
  ALTER TABLE discount_rules ADD COLUMN rule_version INT DEFAULT 1;
  ```

### **4. Mixing Rule Logic with Data**
- Keep rules separate from entities (e.g., don’t store rules in `products` table).
- Bad: `products(discount_value, tiers_affected)`.
- Good: `products(price, ...)` + `discount_rules(applies_to_product_id, ...)`.

### **5. Forgetting to Test Edge Cases**
- Test:
  - Overlapping rules (e.g., 10% + 20%).
  - Inactive rules.
  - Rules with `NULL` values.

---

## **Key Takeaways**

✅ **Rule tables** move logic from code to data, making it easier to update.
✅ **Dynamic queries** reduce app load but require careful indexing.
✅ **Materialized views** speed up reads but need refresh logic.
✅ **Hybrid approaches** balance flexibility and performance.
✅ **Start simple**, then optimize as rules grow in complexity.
✅ **Always test** edge cases and performance.

---

## **Conclusion**
Model Evaluation Patterns help decouple business logic from your application, making your system more flexible and maintainable. By externalizing rules into the database or a dedicated layer, you:
- Reduce app complexity.
- Enable faster iterations on business logic.
- Improve performance with optimized queries.

**Next Steps**:
1. Audit your current rules—are any candidates for externalization?
2. Start small: Add a `discount_rules` table and test it.
3. Gradually migrate complex logic to the DB or a rule engine.

Would you like a follow-up post diving deeper into a specific implementation (e.g., using Redis for caching rules)? Let me know in the comments!

---
```