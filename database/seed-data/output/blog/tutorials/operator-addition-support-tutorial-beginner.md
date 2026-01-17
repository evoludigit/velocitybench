```markdown
# **"Operator Addition": Scaling Filters Like a Pro in Your API**

*Creating flexible, future-proof filtering without breaking existing code*

---

## **Introduction**

Imagine you're building an e-commerce backend where users can filter products by price, category, or availability. At launch, you start with basic operators like `=` (equals) and `>` (greater than). Things work fine—until users ask for "products under $50 *and* in stock." Suddenly, you’re adding `AND`/`OR` logic. Then they want "products *not* in the 'Out of Stock' category." Now you’re adding `NOT`. Before long, you’ve written a patchwork of special cases, and your filter logic is a tangled mess.

This is a common struggle: **your API’s filter system starts simple but quickly becomes rigid as requirements evolve**. The **"Operator Addition"** pattern is a clean, scalable way to add new filter operators (like `NOT`, `BETWEEN`, `IN`, or even custom ones) without rewriting your entire query logic. It’s a real-world pattern used in APIs like [Postman’s API Network](https://www.postman.com/), [FastAPI](https://fastapi.tiangolo.com/) (with dependency injection), and even in internal systems at companies like Airbnb and Uber.

In this post, we’ll:
1. Explain why simple filter systems fail and how this pattern solves it.
2. Walk through a step-by-step implementation in Django (with Python) and Prisma (with TypeScript).
3. Cover tradeoffs, common mistakes, and how to test operator addition safely.

Let’s dive in.

---

## **The Problem: "Operator Overload" in APIs**

Most beginners start with a simple filter system like this:

```python
# Django example: naively adding operators
def filter_products(request):
    query = Product.objects.all()
    if 'price' in request.GET:
        price = request.GET['price']
        query = query.filter(price__gt=price)  # Only > works for now
    return query
```

Or in Prisma/TypeScript:
```typescript
function filterProducts(price?: string) {
  let query = prisma.product.findMany();
  if (price) {
    query = query.where(price_GT: parseFloat(price)); // Only GT
  }
  return query;
}
```

**This approach fails when:**
1. **You need to add a new operator**: To support `AND/OR`, you must rewrite the entire filter function. Suddenly, you’re juggling if-statements like:
   ```python
   if 'price' in request.GET and 'category' in request.GET:
       query = query.filter(AND(
           price__gt=price,
           category=request.GET['category']
       ))
   ```
   This violates the **DRY principle** and introduces bugs.

2. **Performance degrades**: Each new operator might require a different SQL query structure. For example, `IN` requires a list, while `BETWEEN` requires two values. Without a pattern, you’re repeating parsing logic.

3. **Backward compatibility breaks**: If you change how filters are parsed, old clients stop working.

4. **Custom operators are impossible**: What if the client wants `price__in_stock_AND_expensive`? Or `name__contains_any_of=["apple", "banana"]`?

This leads to **"operator overload"**—a system where adding features becomes a chore, and maintaining it is painful.

---

## **The Solution: Operator Addition Pattern**

The **Operator Addition** pattern allows you to:
- **Decouple parsing from execution**: Separate how the operator is parsed (e.g., `NOT price__gt=100`) from how it’s applied (e.g., using Django’s `Q` objects or Prisma’s chainable methods).
- **Support operators dynamically**: Add `NOT`, `BETWEEN`, `IN`, or custom operators without rewriting the core logic.
- **Keep backward compatibility**: Old clients keep working while new ones get the latest features.

At its core, this pattern uses:
1. **Operator mapping**: A dictionary or registry that maps operator strings (e.g., `NOT`, `IN`) to functions.
2. **Query builders**: A system to chain these operators into valid SQL/TypeORM/Prisma queries.
3. **Request parsing**: Extracting operator/value pairs from the request (e.g., `?price=NOT__gt=100`).

---

## **Implementation Guide**

Let’s implement this in **Django (Python)** first, then **Prisma (TypeScript)**. Both examples use a **"sanitized query string"** format like:
```
?price__NOT__gt=100&category=electronics
```

### **1. Django (Python) Implementation**
#### **Step 1: Define Operator Mappings**
Create a registry of supported operators and how they map to Django’s `Q` objects.

```python
# filters/registry.py
from django.db.models import Q

OPERATORS = {
    # Basic operators
    'gt': ('__gt',),
    'gte': ('__gte',),
    'lt': ('__lt',),
    'lte': ('__lte',),
    'exact': ('=',),
    'contains': ('__contains',),
    'in': ('__in',),

    # Advanced operators (requires the pattern)
    'NOT': lambda field, value: ~Q(**{f"{field}": value}),
    'BETWEEN': lambda field, low, high: Q(**{f"{field}__gte": low, f"{field}__lte": high}),
}
```

#### **Step 2: Parse the Request**
Extract operator/value pairs from the query string.

```python
# filters/parser.py
from urllib.parse import parse_qs
import re

def parse_filter_params(params):
    filters = {}
    for key, values in params.items():
        # Split on double underscores (e.g., "price__NOT__gt=100")
        parts = key.split('__')
        if len(parts) < 2:
            continue  # Skip simple filters like ?price=100

        field = '_'.join(parts[:-1])
        operator = parts[-1]

        # Handle edge cases like "NOT__gt"
        if '__' in operator:
            operator_parts = operator.split('__')
            if len(operator_parts) > 1:
                # e.g., "NOT__gt" -> operator="NOT", sub_operator="gt"
                op = operator_parts[0]
                sub_op = operator_parts[1]
                filters.setdefault(field, {}).setdefault(op, []).append((sub_op, values[0]))
            else:
                filters[field] = operator
        else:
            filters[field] = operator
    return filters
```

#### **Step 3: Build the Query**
Apply the parsed filters to the manager.

```python
# filters/query_builder.py
from django.db.models import Q
from .registry import OPERATORS

def build_query(manager, filters):
    query_parts = []

    for field, ops in filters.items():
        if isinstance(ops, str):  # Simple operator (e.g., "contains")
            op = ops
            value = next(iter(manager.model._meta.get_field_by_name(field)[0].get_prep_lookup(value)[1]))
            query_parts.append(Q(**{f"{field}__{op}": value}))
        else:  # Complex operator (e.g., {"NOT": [("gt", "100")]})
            for op, (sub_op, value) in ops.items():
                if op not in OPERATORS:
                    raise ValueError(f"Unsupported operator: {op}")

                if op == 'NOT':
                    sub_query = OPERATORS[sub_op](field, value)
                    query_parts.append(~sub_query)
                elif op == 'BETWEEN':
                    low, high = value.split(',')
                    sub_query = OPERATORS[op](field, low, high)
                    query_parts.append(sub_query)
                else:
                    query_parts.append(Q(**{f"{field}__{OPERATORS[op][0]}": value}))

    return Q(*query_parts) if query_parts else Q(True)
```

#### **Step 4: Use It in a View**
Now your view can handle complex filters:

```python
# views.py
from django.db.models import Q
from filters.query_builder import build_query
from .models import Product

def product_list(request):
    filters = parse_filter_params(request.GET)
    query = build_query(Product.objects, filters)
    products = Product.objects.filter(query)
    return Response({"products": list(products.values())})
```

**Example Request:**
```
GET /products/?price__NOT__gt=100&category__contains=electronics
```
**Result:**
```sql
SELECT "products"."id", ... FROM "products"
WHERE (
    NOT (price > 100) AND
    category LIKE '%electronics%'
)
```

---

### **2. Prisma (TypeScript) Implementation**
For Prisma, we’ll use a similar approach but with TypeScript. Here’s how you’d structure it:

#### **Step 1: Define Operator Registry**
```typescript
// src/filters/registry.ts
import { Prisma } from '@prisma/client';

type OperatorFn = (field: string, value: string | string[]) => Prisma.PrismaPromise<any>;

export const OPERATORS: Record<string, OperatorFn> = {
    gt: (field, value) => ({ [field]!: { gt: parseFloat(value) } }),
    gt: (field, value) => ({ [field]!: { gt: value } }),
    contains: (field, value) => ({ [field]!: { contains: value } }),
    in: (field, value) => ({ [field]!: { in: value.split(',') } }),

    // Custom operator example
    is_expensive: (field) => ({ price: { gt: 100 } }),
};
```

#### **Step 2: Parse Request**
```typescript
// src/filters/parser.ts
export function parseFilterParams(params: Record<string, string[]>) {
    const filters: Record<string, { operator: string; value: string }[]> = {};

    for (const [key, values] of Object.entries(params)) {
        const parts = key.split('__');
        if (parts.length < 2) continue;

        const field = parts.slice(0, -1).join('__');
        const operator = parts[parts.length - 1];

        // Handle nested operators like "NOT__gt"
        if (operator.includes('__')) {
            const [op, subOp] = operator.split('__');
            filters[field]?.push({ operator: op, value: `${subOp}=${values[0]}` }) ||
                filters[field] = [{ operator: op, value: `${subOp}=${values[0]}` }];
        } else {
            filters[field]?.push({ operator, value: values[0] }) ||
                filters[field] = [{ operator, value: values[0] }];
        }
    }
    return filters;
}
```

#### **Step 3: Build Prisma Query**
```typescript
// src/filters/query_builder.ts
import { Prisma } from '@prisma/client';
import { OPERATORS } from './registry';

export function buildPrismaQuery(filters: Record<string, any>) {
    let query: Prisma.ProductWhereInput = {};

    for (const [field, ops] of Object.entries(filters)) {
        for (const { operator, value } of ops) {
            if (operator === 'NOT') {
                // Handle "NOT__gt=100" -> `NOT (price > 100)`
                const [subOp, val] = value.split('=');
                query = {
                    ...query,
                    NOT: OPERATORS[subOp](field, val),
                };
            } else if (operator === 'BETWEEN') {
                // Handle "price__BETWEEN=100,200" -> `price BETWEEN 100 AND 200`
                const [low, high] = value.split(',');
                query = {
                    ...query,
                    [field]: {
                        gte: parseFloat(low),
                        lte: parseFloat(high),
                    },
                };
            } else {
                // Simple operator
                query = {
                    ...query,
                    [field]: OPERATORS[operator](field, value),
                };
            }
        }
    }

    return query;
}
```

#### **Step 4: Use in a Route**
```typescript
// src/pages/api/products.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { prisma } from '@/prisma';
import { parseFilterParams } from '@/filters/parser';
import { buildPrismaQuery } from '@/filters/query_builder';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
    const filters = parseFilterParams(req.query);
    const query = buildPrismaQuery(filters);
    const products = prisma.product.findMany({ where: query });
    res.status(200).json(products);
}
```

**Example Request:**
```
GET /api/products?price__NOT__gt=100&category__contains=electronics
```
**Result:**
```typescript
// Prisma generates:
{
  where: {
    AND: [
      { NOT: { price: { gt: 100 } } },
      { category: { contains: "electronics" } },
    ],
  },
}
```

---

## **Common Mistakes to Avoid**

1. **Hardcoding query strings**:
   Avoid parsing filters with regex hacks (e.g., `price__NOT__gt=100` → `price > 100` manually). Use a structured registry like `OPERATORS`.

2. **Ignoring SQL injection**:
   Always sanitize inputs. In Django, use `Q` objects carefully (they’re safe if used with model fields). In Prisma, ensure `value` is parsed correctly (e.g., `parseFloat` for numeric values).

3. **Assuming all operators are supported**:
   Validate operators in `OPERATORS` before applying them. Raise a clear error if an unsupported operator is used.

4. **Not testing edge cases**:
   Test:
   - Empty filters (`?` → return all).
   - Invalid operators (`?price__INVALID=100` → error).
   - Nested operators (`?price__NOT__IN=100,200` → `price NOT IN (100, 200)`).

5. **Overcomplicating the parser**:
   Start simple (e.g., `parse_qs`) and only add complexity when needed (e.g., nested operators).

---

## **Key Takeaways**
- **Operator Addition** lets you **scale filter operators without rewriting code**.
- **Decouple parsing from execution**: Use a registry to map operators to query builders.
- **Support backward compatibility**: Old clients keep working while you add new operators.
- **Tradeoffs**:
  - **Pros**: Clean, maintainable, extensible.
  - **Cons**: Slightly more boilerplate upfront; requires careful testing.
- **Tools to use**:
  - Django: `Q` objects for dynamic queries.
  - Prisma: Chained `where` clauses.
  - TypeScript: Type-safe operator registries.

---

## **Conclusion**

Operator Addition is a **simple but powerful pattern** for building flexible, future-proof APIs. Whether you’re filtering products, articles, or user data, this pattern ensures your system can evolve without breaking:

| Problem               | Solution                          | Example                                                                 |
|-----------------------|-----------------------------------|-------------------------------------------------------------------------|
| Need more operators   | Add to registry                   | `OPERATORS["BETWEEN"] = ...`                                            |
| Complex queries       | Chain operators dynamically       | `Q(AND(~Q(price__gt=100), category="electronics"))`                     |
| Backward compatibility| Parse requests uniformly          | `?price__gt=100` → `price > 100` (always works)                        |

**Next steps:**
1. Start small: Add one new operator (e.g., `NOT`) to your existing filter system.
2. Test thoroughly: Cover happy paths and edge cases.
3. Extend gradually: Add `BETWEEN`, `IN`, or custom operators as needed.

By adopting this pattern, you’ll avoid the "patchwork API" trap and build systems that grow with your users’ needs. Happy coding! 🚀

---
### **Further Reading**
- [FastAPI Filtering with Dependency Injection](https://fastapi.tiangolo.com/advanced/custom-operators/)
- [PostgreSQL’s `jsonb` for Dynamic Filtering](https://www.postgresql.org/docs/current/datatype-json.html)
- [Prisma’s `where` Clauses](https://www.prisma.io/docs/concepts/components/prisma-client/querying-relational-data#filtering)

---
**Got questions?** Drop them in the comments or tweet me at [@backend_edu](https://twitter.com/backend_edu). I’d love to hear how you’re using this pattern!
```