---

# **Mutation Response Contract: Enforcing Predictable API Responses with Stored Procedures**

Designing robust APIs isn’t just about writing clean code—it’s about ensuring your backend behaves predictably. When clients call your API, they expect a specific structure in response, especially after mutations. If your stored procedures return raw data (like `SELECT * FROM users` after an insert), you risk exposing internal schema changes, breaking client expectations, and making future updates painful.

This is where the **Mutation Response Contract** pattern comes in. It ensures that every stored procedure returns consistent, well-defined responses that match a predefined API contract. By abstracting the underlying database changes from your response payload, you achieve better maintainability, safer refactoring, and happier frontend developers who can rely on your API’s contract.

In this post, we’ll explore:
- Why raw procedure responses are problematic
- How the Mutation Response Contract pattern solves this
- Practical SQL and API examples
- Common pitfalls and best practices

---

## **The Problem: Inconsistent and Unmaintainable Responses**

Let’s start with a common scenario. Suppose you build an eCommerce API where users can create orders via a stored procedure:

```sql
CREATE PROCEDURE create_order(
    user_id INT,
    total DECIMAL(10,2),
    items JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO orders(user_id, total, items, status)
    VALUES(user_id, total, items, 'pending');

    RETURN QUERY SELECT * FROM orders WHERE id = CURRVAL();
END;
$$;
```

When a client calls this procedure, they get back a raw record from the `orders` table. But here’s the problem:

1. **Leaking Schema Changes**: If you later add a `created_at` column, clients that expect only `id`, `user_id`, `total`, and `items` will break.
2. **Unpredictable Fields**: Third-party integrations might rely on specific fields, and a change in your database schema could invalidate their logic.
3. **No Standardization**: Some procedures return a single record, others return a list—no consistent contract.

Worse yet, if your API ever changes the return type (e.g., to include nested user details), backward compatibility is shattered.

---
## **The Solution: Mutation Response Contract**

The **Mutation Response Contract** pattern enforces that every stored procedure—whether it creates, updates, deletes, or queries data—returns a response that adheres to a predefined structure. This contract can be defined in:
- A schema documentation (OpenAPI/Swagger)
- A backend API specification (like GraphQL schemas or JSON contracts)
- A database layer (via views or functions that standardize responses)

By applying this pattern, you ensure:
✅ **Predictable payloads**: Clients always receive the same fields, even if the underlying schema evolves.
✅ **Backward compatibility**: New fields can be added without breaking existing consumers.
✅ **Security**: Sensitive internal fields (like `password_hash`) are never exposed.
✅ **Easier refactoring**: You can safely change the database table schema without fear of API breakage.

---

## **Components of the Mutation Response Contract**

The pattern combines three key components:

1. **Contract Definition**
   A standardized response schema that all mutations must follow. This could be a JSON schema, a GraphQL type, or a SQL view.

2. **Response Standardization Layer**
   A SQL layer (e.g., a view, function, or trigger) that transforms raw DB results into the contract.

3. **API Layer Enforcement**
   Your API layer (e.g., REST, GraphQL) ensures that every mutation returns the contract-compliant response.

---

## **Step-by-Step Implementation**

Let’s refactor the `create_order` example to enforce a response contract.

### **Step 1: Define the Response Contract**
First, document the expected response structure. For our eCommerce API, we want:

```json
{
  "id": "string (UUID)",
  "user_id": "string",
  "total": "number",
  "items": "[{ product_id: string, quantity: number }]",
  "status": "string (enum: pending, completed, cancelled)",
  "created_at": "string (ISO-8601)"
}
```

### **Step 2: Standardize the Database Response**
Instead of returning raw DB rows, we’ll create a **contract-aligned view** or function.

#### Option A: Using a SQL View
```sql
-- Create a view that enforces the contract
CREATE OR REPLACE VIEW vw_orders_contract AS
SELECT
    id AS record_id,
    user_id,
    total,
    items,
    status,
    created_at,
    -- Add computed fields if needed
    CASE WHEN status = 'pending' THEN false ELSE true END AS is_completed
FROM orders;
```

#### Option B: Using a SQL Function (More Flexible)
```sql
CREATE OR REPLACE FUNCTION get_order_contract(p_order_id INT)
RETURNS TABLE (
    record_id UUID,
    user_id INT,
    total DECIMAL(10,2),
    items JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP,
    is_completed BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.user_id,
        c.total,
        c.items,
        c.status,
        c.created_at,
        CASE WHEN c.status = 'pending' THEN false ELSE true END AS is_completed
    FROM orders c
    WHERE c.id = p_order_id;
END;
$$ LANGUAGE plpgsql;
```

#### Option C: Using a View with a Materialized View (For Batch Operations)
If you need to fetch multiple records (e.g., all orders for a user), you can enforce the same contract on a view:

```sql
CREATE OR REPLACE VIEW vw_user_orders AS
SELECT
    o.id AS record_id,
    o.user_id,
    o.total,
    o.items,
    o.status,
    o.created_at,
    CASE WHEN o.status = 'pending' THEN false ELSE true END AS is_completed
FROM orders o;
```

### **Step 3: Update Your Stored Procedure to Use the Contract**
Now, refactor `create_order` to return the contract instead of raw data:

```sql
CREATE OR REPLACE PROCEDURE create_order(
    p_user_id INT,
    p_total DECIMAL(10,2),
    p_items JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id UUID;
BEGIN
    INSERT INTO orders(user_id, total, items, status)
    VALUES(p_user_id, p_total, p_items, 'pending');
    GET DIAGNOSTICS v_order_id = RETURNED_ID;

    -- Return the contract-aligned response
    RETURN QUERY
    SELECT *
    FROM get_order_contract(v_order_id);
END;
$$;
```

### **Step 4: API Layer Enforcement**
Your backend API (e.g., FastAPI, Express, or a GraphQL resolver) should ensure that all mutations return the contract. For example, in a REST API:

```python
# FastAPI Example
from fastapi import FastAPI
from typing import Dict, Any

app = FastAPI()

@app.post("/orders", response_model=OrderContract)
def create_order(user_id: int, total: float, items: list[Dict[str, Any]]):
    # Call the stored procedure
    response = db.execute("CALL create_order(%s, %s, %s)", (user_id, total, json.dumps(items)))
    return response.one()  # Ensures the contract is returned
```

```json
# OpenAPI (Swagger) Contract Example
components:
  schemas:
    OrderContract:
      type: object
      properties:
        record_id:
          type: string
          format: uuid
        user_id:
          type: integer
        total:
          type: number
          format: float
        items:
          type: array
          items:
            type: object
            properties:
              product_id:
                type: string
              quantity:
                type: integer
        status:
          type: string
          enum: [pending, completed, cancelled]
        created_at:
          type: string
          format: date-time
        is_completed:
          type: boolean
```

### **Step 5: Handle Edge Cases**
- **Error Responses**: Ensure your contract includes error fields (e.g., `errors: [{"code": string, "message": string}]`).
- **Partial Updates**: If mutations return nothing (e.g., a `PUT /users/:id`), return a `204 No Content` with no body.
- **Pagination**: For list operations, standardize the response format (e.g., `{ "items": [...], "page": { ... } }`).

---

## **Common Mistakes to Avoid**

1. **Overly Complex Contracts**
   Don’t force every mutation to return the same fields. Use conditional logic to include relevant data (e.g., omit `items` in a `GET /orders` response if the user doesn’t have permission).

2. **Ignoring Performance**
   Contract-aligned views can slow down mutations. Benchmark and optimize if needed (e.g., use materialized views for read-heavy apps).

3. **Breaking Backward Compatibility**
   When evolving the contract, always document deprecation policies (e.g., add a `deprecated` field before removing data).

4. **Hardcoding Fields**
   Avoid hardcoding all fields in views. Use dynamic SQL or parameters to allow flexibility (e.g., only return fields the client requested).

5. **Not Testing Contract Compliance**
   Write unit tests to verify that every stored procedure returns the correct contract. Tools like SQLFluff or custom scripts can help.

---

## **Key Takeaways**

- **Problem**: Raw stored procedure responses expose schema changes and lack consistency.
- **Solution**: Enforce a **Mutation Response Contract** to standardize outputs.
- **Implementation**:
  - Define a contract (JSON schema, GraphQL type, or SQL view).
  - Create a response standardization layer (views, functions).
  - Ensure API layers return the contract.
- **Best Practices**:
  - Start with minimal viable contracts and expand as needed.
  - Balance standardization with performance.
  - Document contracts clearly for clients and internal teams.
- **Tradeoffs**:
  - **Pros**: Predictability, backward compatibility, security.
  - **Cons**: Slight overhead in development and maintenance.

---

## **Conclusion**

The Mutation Response Contract pattern is a simple yet powerful way to tame the chaos of database-driven APIs. By standardizing how your backend returns data, you reduce technical debt, protect clients from breaking changes, and make your system more maintainable.

Start small—apply the pattern to critical mutations first. Over time, you’ll find that it becomes a cornerstone of your API design, allowing you to refactor with confidence.

**Next Steps**:
- Audit your existing procedures. Which ones could benefit from a contract?
- Experiment with a few high-impact mutations first.
- Share the pattern with your team to build consistency across the codebase.

Happy coding! 🚀