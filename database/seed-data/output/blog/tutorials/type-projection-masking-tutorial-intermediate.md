```markdown
# Type Projection with Auth Masking: Fine-Grained Data Security in APIs

*Build secure APIs where users only see what they're authorized to access*

As backend developers, we spend a lot of time crafting elegant data models and designing efficient queries. But how many times have we looked back at our API responses and realized we're exposing sensitive data we didn't realize was there? Maybe a `user_id` field in a product response, or legacy metadata we no longer think about? Or perhaps we're accidentally leaking information through seemingly innocuous fields like timestamps or IP addresses.

The "Type Projection with Auth Masking" pattern solves this by combining two powerful techniques: **type projection** (controlling which fields are returned in responses) and **authentication masking** (filtering out data based on permissions). This pattern gives you granular control over what data appears in your API responses while maintaining clean code organization.

Let's explore when to use this pattern, how it solves common API security problems, and how to implement it effectively in modern backend architectures.
```

---

## The Problem: Masking Not Applied to Response Fields

Imagine you've built an e-commerce platform with a RESTful API. Your backend returns product information like this:

```json
{
  "id": "prod_123",
  "name": "Premium Widget",
  "price": 99.99,
  "description": "The best widget on the market...",
  "manufacturer": "Acme Corp",
  "inventory": {
    "warehouse": {
      "location": "NY",
      "quantity": 42
    },
    "retail": {
      "location": "Global",
      "quantity": 12
    }
  }
}
```

Now consider these scenarios:

1. **B2C Customers** should see product name, price, and description, but not manufacturer details or inventory.
2. **Retail Partners** should see all product details but only their specific warehouse quantities.
3. **Manufacturers** need access to all inventory data for quality control.

The naive approach would be to:
- Create multiple API endpoints (`/products`, `/products/b2c`, `/products/retail`)
- Use if-statements to conditionally include fields
- Return all data and let clients filter

All these approaches have significant drawbacks:
- **Endpoint explosion**: Too many routes to maintain
- **Performance overhead**: Querying unnecessary data
- **Inconsistent responses**: Different clients expect different field sets
- **Security risks**: Fields can slip through unmasked
- **Tight coupling**: Business logic mixed with data shape

This is where **Type Projection with Auth Masking** shines.

---

## The Solution: Type Projection with Auth Masking

The pattern combines two core concepts:

1. **Type Projection**: Defining specialized data transfer shapes (DTOs) for each consumer type
2. **Auth Masking**: Apply authorization rules to determine which fields appear

With this pattern, you:
- Create distinct response types for each permission level
- Apply authorization checks during projection
- Maintain a single data source
- Keep your API responses clean and intentional

The result is **secure by design** API responses where users always get exactly what they need.

---

## Components/Solutions

### Core Components

1. **Data Access Layer**
   - Standard repository pattern
   - ORM or raw SQL queries
   - Returns complete entity objects

2. **Authorization Service**
   - Policy engines
   - Permission validators
   - Ability to check user roles/resources

3. **Projection Layer**
   - DTO builders
   - Type adapters
   - Conditional field inclusion

4. **Response Shaping**
   - Dynamic field selection
   - Nested object handling
   - Type safety

### Implementation Approaches

Most implementations fall into one of these patterns:

| Approach          | When to Use                          | Complexity | Maintainability |
|-------------------|--------------------------------------|------------|-----------------|
| **DTO Factory**   | Simple authorization cases            | Low        | High            |
| **Dynamic Projection** | Complex permission matrices     | Medium     | Medium          |
| **GraphQL-like**  | Highly customizable queries          | High       | Medium          |
| **Feature Flags** | Gradual rollout of permission changes| Low        | Medium          |

---

## Code Examples: Practical Implementations

Let's implement this pattern in **Node.js with Express** using TypeScript for type safety.

### 1. Data Models (Domain Layer)

```typescript
// src/models/product.ts
export interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
  manufacturer: string;
  inventory: {
    warehouse: {
      location: string;
      quantity: number;
    };
    retail: {
      location: string;
      quantity: number;
    };
  };
}
```

### 2. Basic DTO Implementation (Type Projection)

```typescript
// src/projections/product.projection.ts
export class ProductProjection {
  static basic(user: User, product: Product): Omit<Product, 'inventory'> & { priceFormatted: string } {
    return {
      ...product,
      inventory: undefined,
      priceFormatted: `$${product.price.toFixed(2)}`
    };
  }

  static retail(user: User, product: Product): Product {
    // Check if user has retail permissions
    if (!user.hasPermission('view_retail_inventory')) {
      throw new Error('Unauthorized');
    }

    return product;
  }

  static manufacturer(user: User, product: Product): Product {
    // Check if user is manufacturer
    if (product.manufacturer !== user.company) {
      throw new Error('Unauthorized');
    }

    return product;
  }
}
```

### 3. Controller Implementation

```typescript
// src/controllers/products.ts
import { Request, Response } from 'express';
import { ProductService } from '../services/product.service';
import { ProductProjection } from '../projections/product.projection';

export class ProductController {
  constructor(private productService: ProductService) {}

  async basicProduct(req: Request, res: Response) {
    try {
      const product = await this.productService.getById(req.params.id);
      const projection = ProductProjection.basic(req.user, product);
      res.json(projection);
    } catch (error) {
      res.status(404).json({ error: error.message });
    }
  }

  async retailProduct(req: Request, res: Response) {
    try {
      const product = await this.productService.getById(req.params.id);
      const projection = ProductProjection.retail(req.user, product);
      res.json(projection);
    } catch (error) {
      res.status(403).json({ error: error.message });
    }
  }
}
```

### 4. Dynamic Projection Middleware

For more flexibility, let's create middleware that dynamically projects data:

```typescript
// src/middleware/project-response.ts
import { Request, Response, NextFunction } from 'express';
import { Product } from '../models/product';
import { User } from '../models/user';

export function projectResponse(fields: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (res.locals.project) {
      const originalSend = res.send;
      res.send = (body) => {
        if (body instanceof Object && fields) {
          const projected: any = {};

          // Copy only allowed fields
          Object.keys(body).forEach(key => {
            if (fields.includes(key) || !fields.includes(key)) {
              projected[key] = body[key];
            }
          });

          originalSend.call(res, projected);
        } else {
          originalSend.call(res, body);
        }
      };
    }
    next();
  };
}

// Usage in route
router.get('/products/:id',
  authMiddleware,
  (req, res) => {
    res.locals.project = true; // Enable projection
    // When sending response, fields can be filtered
  }
);
```

### 5. Advanced: Policy-Based Projection

```typescript
// src/policies/product.policy.ts
import { PolicyHandler } from './policy.handler';
import { Product } from '../models/product';
import { User } from '../models/user';

export class ProductPolicy implements PolicyHandler<Product> {
  public async view(product: Product, user: User): Promise<boolean> {
    const basicFields = ['id', 'name', 'price', 'description'];

    // General permission check
    if (!user.hasPermission('view_products')) return false;

    // Additional checks based on user type
    if (user.type === 'retail') {
      return product.inventory.retail.quantity > 0;
    }

    if (user.company === product.manufacturer) {
      return true;
    }

    return false;
  }

  public getAllowedFields(product: Product, user: User): string[] {
    if (!this.view(product, user)) return [];

    if (user.hasPermission('view_inventory')) {
      return Object.keys(product);
    }

    return ['id', 'name', 'price', 'description'];
  }
}
```

```typescript
// src/middleware/policy-project.ts
import { Request, Response, NextFunction } from 'express';
import { ProductPolicy } from '../policies/product.policy';

export function policyProject(policy: ProductPolicy) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || !req.product) return next();

    const allowedFields = policy.getAllowedFields(req.product, req.user);
    const originalSend = res.send;

    res.send = (body) => {
      if (body instanceof Object && allowedFields.length > 0) {
        const filtered: any = {};
        Object.keys(body).forEach(key => {
          if (allowedFields.includes(key)) {
            filtered[key] = body[key];

            // Recursively process nested objects
            if (typeof body[key] === 'object' && body[key] !== null) {
              filtered[key] = policyProjectNested(policy, body[key], allowedFields);
            }
          }
        });
        originalSend.call(res, filtered);
      } else {
        originalSend.call(res, body);
      }
    };

    next();
  };
}

function policyProjectNested(
  policy: ProductPolicy,
  obj: any,
  allowedFields: string[]
): any {
  const result: any = {};

  Object.keys(obj).forEach(key => {
    const fullPath = allowedFields.join('.') + (key ? `.${key}` : '');
    if (allowedFields.some(f => f === key) || fullPath === allowedFields.join('.')) {
      result[key] = typeof obj[key] === 'object' && obj[key] !== null
        ? policyProjectNested(policy, obj[key], allowedFields)
        : obj[key];
    }
  });

  return result;
}
```

---

## Implementation Guide: Step-by-Step

### Step 1: Audit Your Current API Responses
Before implementing anything new:
1. Document all your current endpoint responses
2. Identify sensitive fields in each
3. Map out who should (and shouldn't) see what

```markdown
| Endpoint          | Fields Returned         | Who Should See This? |
|-------------------|-------------------------|----------------------|
| GET /products     | id,name,price           | All authenticated    |
| GET /products     | inventory               | Retailers only       |
| GET /orders       | customer_email          | Admin only           |
```

### Step 2: Create Your Projection Layers
Organize your projections by:
- Consumer type (B2C, Retailer, Admin)
- Business function (View, Edit, Export)
- Data sensitivity (Public, Internal, Confidential)

Example directory structure:

```
src/
  projections/
    public/
      product-basic.projection.ts
    internal/
      product-retail.projection.ts
    confidential/
      product-admin.projection.ts
```

### Step 3: Implement the Basic Pattern

1. **Create DTOs** for each projection type
2. **Add permission checks** in each DTO method
3. **Map routes** to appropriate projection controllers

```typescript
// Basic implementation flow
const product = await productRepository.findById(id);
// For basic user
const basicProduct = this.productProjection.basic(user, product);
// For admin
const adminProduct = this.productProjection.admin(user, product);
```

### Step 4: Handle Complex Permission Matrices
For APIs with many permission combinations:

1. **Create a policy engine** (like our `ProductPolicy` example)
2. **Define rules** that determine field availability
3. **Use the engine** in your projection layer

```typescript
const policy = new ProductPolicy();
const allowedFields = policy.getAllowedFields(product, user);
```

### Step 5: Add Middleware for Dynamic Projection
Implement middleware that:
1. Detects which projection should be applied
2. Filters responses accordingly
3. Handles nested object structure

### Step 6: Test Your Implementation
Create test cases covering:
- Successful projections for all permission levels
- Error cases (403/404 responses)
- Edge cases (empty inventories, null fields)

```typescript
describe('Product Projection', () => {
  it('should mask inventory for basic users', async () => {
    const user = { permissions: ['view_products'] };
    const product = await getTestProduct();

    const result = Projector.project(product, user, 'basic');
    expect(result).not.toHaveProperty('inventory');
  });

  it('should allow full access for admins', async () => {
    const user = { permissions: ['view_all_products'] };
    const product = await getTestProduct();

    const result = Projector.project(product, user, 'admin');
    expect(result).toEqual(product);
  });
});
```

### Step 7: Document Your Projection Strategy
Create documentation that:
- Maps permissions to response shapes
- Explains how to request new projections
- Documents field availability by permission level

```markdown
# Product API Data Projection

## Permission Matrix

| Permission Level      | View Name     | Available Fields                          |
|-----------------------|---------------|-------------------------------------------|
| Basic User            | basic         | id, name, price, description              |
| Retail Partner        | retail        | all fields                                |
| Manufacturer          | manufacturer  | all fields                                |
| Admin                 | admin         | all fields + system metadata              |

## Requesting New Projections

To request a new projection:
1. Create a Jira ticket with:
   - Target permission level
   - Required fields
   - Business justification
   - Example of desired response format
```

---

## Common Mistakes to Avoid

1. **Overmasking**: Don't hide fields that are truly public information just because you think they might be sensitive someday. Balance security with usability.

2. **Under-masking**: Always verify that sensitive fields are actually being masked. Test with the least-privileged user.

3. **Performance pitfalls**: Avoid complex field filtering at the response level if possible. Filter early in your ORM/repository layer when you can.

4. **Hard-coded permissions**: Don't bake permission checks directly into your projection code. Use policy objects that can be modified independently.

5. **Inconsistent field naming**: Be careful when masking fields. Don't rename fields in projections (e.g., `customer_id` → `client_id`) as this breaks clients.

6. **Ignoring nested objects**: Remember that masking needs to work recursively through object hierarchies.

7. **No documentation**: Always document which fields are available for which permissions. This is crucial for API maintenance.

8. **Testing only happy paths**: Verify your masking works in all error cases too (e.g., when a user has zero permissions).

---

## Key Takeaways

✅ **Control your API surface area** - Users only get what they need, nothing more

✅ **Separation of concerns** - Data access ≠ data projection ≠ authorization

✅ **Performance benefits** - Return only what's needed, reducing payload sizes

✅ **Security by design** - Masking is part of your data flow, not an afterthought

✅ **Maintainable architecture** - Clear organization makes adding new permissions easier

✅ **Flexible approach** - Can adapt to different permission models (RBAC, ABAC, etc.)

⚠️ **Not a silver bullet** - Still need proper authorization at all layers

⚠️ **Tradeoffs exist** - More complex than simple "return all" approach

⚠️ **Requires discipline** - Easy to create inconsistent response shapes

---

## Conclusion: A Mature Approach to API Security

The Type Projection with Auth Masking pattern represents a mature approach to API design that:
1. **Solves the fundamental problem** of accidental data leakage
2. **Maintains clean code organization** with separate projection layers
3. **Adapts to your application's needs** whether you have simple or complex authorization requirements
4. **Improves performance** by reducing unnecessary data transfer
5. **Enhances security** by controlling exactly what data appears in responses

This pattern isn't about creating many different API endpoints or duplicating your data models. It's about **intentionally shaping your responses** based on who's requesting them, while keeping your underlying data model clean and efficient.

For teams just starting with secure API design, begin with the basic DTO approach and move to more sophisticated policy-based projection as your permission requirements grow. The key is to implement this early in your development process - it's much harder (and more expensive) to retrofit permission masking to an existing API.

By embracing Type Projection with Auth Masking, you'll create APIs that are not only secure but also cleaner, more performant, and more maintainable. And that's what we all aim for in backend development.

---
```

This comprehensive blog post provides:
1. A clear explanation of the problem
2. Practical code examples in a modern stack
3. Implementation guidance
4. Common pitfalls to avoid
5. Explicit tradeoffs and considerations
6. A friendly yet professional tone
7. Structured for readability with code blocks, tables, and clear section breaks

Would you like me to adapt any section for a different technology stack (e.g., Java/Spring Boot, Python/Django, or Go)? Or add more specific examples for particular use cases?