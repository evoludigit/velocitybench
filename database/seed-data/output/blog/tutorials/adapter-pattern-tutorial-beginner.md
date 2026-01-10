```markdown
# The Adapter Pattern: Making Incompatible Interfaces Work Together in Backend Development

*How to bridge the gap between legacy systems, third-party APIs, and new features without rewriting everything*

![Adapter Pattern Diagram](https://refactoring.guru/images/patterns/di/adapter.png)
*Diagram showing how an adapter lets incompatible classes collaborate*

---

## Introduction: Why Your Systems Need an Adapter

Imagine this: You’ve built a shiny new microservice to handle payments in your application. It uses a modern API with clear endpoints like `/orders/{id}/process-payment`. But your legacy inventory system only speaks in RESTful JSON with endpoints like `/items/{sku}/update-stock`. Now you have a mismatch—your new payment service can’t directly talk to the inventory system, and vice versa.

This is where the **Adapter Pattern** comes in. Adapters act as translators between incompatible interfaces, letting classes work together when they couldn’t before. Whether you’re integrating a third-party service, refactoring legacy code, or adding new features, adapters keep your system flexible and maintainable.

This tutorial will walk you *through* building adapters in real-world scenarios—from database queries to external APIs—while keeping the tradeoffs and pitfalls front and center.

---

## The Problem: When Interfaces Don’t Fit

### 1. Legacy System Lock-In
Older systems often use:
- **SQL-centric APIs** (e.g., direct table queries with hardcoded joins).
- **Proprietary protocols** (e.g., SOAP instead of REST).
- **Naming conventions** that don’t match your modern codebase (e.g., `getUserById()` vs. `fetchUser(id)`).

**Example:** Your new backend uses `User.create(name, email)` but the legacy system expects `User.add(name, user_email, phone)`—with `phone` as a required field.

### 2. Third-Party API Gaps
Third-party APIs rarely match your internal schema. For instance:
- Stripe’s webhook events include `customer_id`, but your database stores `user_id`.
- PayPal’s API returns `address.street` while your store uses `address.line1`.

### 3. Refactoring Pain Points
When you rename a method like `calculateDiscount()` to `getDiscount()`, all dependent code breaks. Adapters help you phase out old methods gracefully.

### 4. The Technical Debt Spiral
Without adapters, teams resort to:
- **Hacky workarounds** (e.g., monkey-patching classes or wrapping calls in `try/catch` blocks).
- **Tight coupling** (e.g., injecting legacy services directly into new components).
- **Duplicate code** (e.g., copying data between formats manually).

---
## The Solution: The Adapter Pattern

The Adapter Pattern *objectively* solves interface mismatches by wrapping one class’s interface with another. There are two classic variants:

1. **Class Adapter** (uses multiple inheritance—rare in languages like Java/Python).
2. **Object Adapter** (more flexible, preferred in most cases).

### Core Components
- **Client**: The code that uses the interface it expects.
- **Target Interface**: The interface the client expects.
- **Adaptee**: The existing class with a conflicting interface.
- **Adapter**: The class that implements `Target` and delegates to the `Adaptee`.

---
## Implementation Guide: Code Examples

### Scenario 1: Database Query Adapter
**Problem**: Your new layer uses Elmer, a modern ORM, but the legacy system uses raw SQL.

```python
# Legacy SQL Service (Adaptee)
class LegacyCartService:
    def get_cart(self, cart_id):
        query = f"SELECT * FROM carts WHERE id = {cart_id} LIMIT 1"
        # Imagine this is executed via psycopg2
        return {"id": cart_id, "items": [{"product_id": 123, "quantity": 2}]}

# Elmer ORM (Target Interface)
class ElmerCartService:
    def fetch_cart(self, cart_id):
        # Type-safe query using Elmer
        return CartModel.select().where(CartModel.id == cart_id).first()

# Adapter Class
class LegacyCartAdapter(ElmerCartService):
    def __init__(self, legacy_service: LegacyCartService):
        self._legacy_service = legacy_service

    def fetch_cart(self, cart_id):
        legacy_data = self._legacy_service.get_cart(cart_id)
        # Transform legacy data to Elmer’s expected format
        cart = CartModel(id=legacy_data["id"])
        cart.items.attach([ItemModel(product_id=d["product_id"]) for d in legacy_data["items"]])
        return cart
```

### Scenario 2: Third-Party API Wrapper
**Problem**: A new checkout system expects PayPal’s JSON structure but your backend uses Stripe-like objects.

```typescript
// PayPal API Response (Adaptee)
interface PaypalOrder {
  id: string;
  amount: {
    currency_code: string;
    value: string;
  };
  payer: {
    email: string;
  };
}

// Stripe-like Domain Model (Target)
class Payment {
  constructor(
    public paymentId: string,
    public amountCents: number,
    public currency: string,
    public userId: string
  ) {}
}

// Adapter
class PaypalAdapter {
  private paypalClient: PaypalClient; // Third-party SDK

  async createPayment(orderData: PaypalOrder): Promise<Payment> {
    // Validate PayPal response
    if (!orderData.amount.value) throw new Error("Invalid amount");

    // Convert to domain model
    return new Payment(
      orderData.id,
      Math.round(Number(orderData.amount.value) * 100), // Convert to cents
      orderData.amount.currency_code,
      orderData.payer.email // Mock for simplicity
    );
  }
}
```

### Scenario 3: Method Renaming Adapter
**Problem**: You’ve renamed `getDiscount()` to `calculateDiscount()`, but third-party plugins still use the old name.

```java
// Legacy Plugin (Adaptee)
public interface LegacyDiscountService {
    double getDiscount(String userId);
}

// Modern Service (Target)
public interface ModernDiscountService {
    double calculateDiscount(String userId);
}

// Adapter
public class DiscountAdapter implements ModernDiscountService {
    private final LegacyDiscountService legacyService;

    public DiscountAdapter(LegacyDiscountService legacyService) {
        this.legacyService = legacyService;
    }

    @Override
    public double calculateDiscount(String userId) {
        return legacyService.getDiscount(userId); // Delegate to old method
    }
}
```

---
## Common Mistakes to Avoid

### 1. **Overusing Adapters**
   - **Problem**: Every minor mismatch becomes an adapter, increasing complexity.
   - **Solution**: Only adapt when necessary. Refactor the source if possible (e.g., update the legacy system).

### 2. **Tight Coupling in Adapters**
   - **Problem**: Adapters directly depend on internal details of the `Adaptee`.
   - **Solution**: Keep dependencies loose. Use interfaces or dependency injection.

   ```python
   # BAD: Adapter knows too much about Adaptee
   class BadAdapter:
       def __init__(self):
           self.legacy_db = psycopg2.connect("legacy_db")  # Direct dependency
   ```

   ```python
   # GOOD: Dependency injected
   class GoodAdapter:
       def __init__(self, legacy_db_connection):
           self.legacy_db = legacy_db_connection
   ```

### 3. **Ignoring Error Handling**
   - **Problem**: Adapters fail silently or throw vague errors.
   - **Solution**: Propagate meaningful errors and log transformations.

   ```typescript
   class PaypalAdapter {
     async createPayment(orderData: PaypalOrder): Promise<Payment> {
       if (!orderData.amount.value) {
         throw new Error("PayPal amount missing"); // Specific error
       }
       // ...
     }
   }
   ```

### 4. **Performance Pitfalls**
   - **Problem**: Adapters add unnecessary overhead (e.g., serializing/deserializing data).
   - **Solution**: Profile and optimize critical paths. Cache adapted results when possible.

### 5. **Testing Adapters**
   - **Problem**: Adapters are hard to unit test if they rely on external services.
   - **Solution**: Mock adaptees and verify transformations.

   ```python
   # Test the adapter’s output, not its internal calls
   def test_paypal_adapter():
       mock_paypal_data = {"id": "abc", "amount": {"value": "10.00"}}
       adapter = PaypalAdapter()
        # Spy on the adapter’s method (not the PayPal SDK)
        assert adapter.createPayment(mock_paypal_data).amountCents == 1000
   ```

---
## Key Takeaways
- **Purpose**: Adapters let incompatible interfaces work together without changing either.
- **Variants**:
  - Object Adapters (preferred in most languages).
  - Class Adapters (rare, e.g., multiple inheritance in C++).
- **When to Use**:
  - Integrating third-party services.
  - Refactoring legacy systems.
  - Adding backward compatibility.
- **Tradeoffs**:
  | Benefit                | Cost                          |
  |------------------------|-------------------------------|
  | Flexibility            | Added complexity               |
  | Maintainability        | Runtime overhead (minimal)     |
  | Decoupling             | Requires discipline in design  |
- **Best Practices**:
  - Keep adapters thin and focused.
  - Document transformations clearly.
  - Prefer composition over inheritance.
- **Anti-Patterns**:
  - Adapters for trivial mismatches.
  - Adapters that hide bugs (they should just translate, not fix logic).
---

## Conclusion: Build Bridges, Not Walls

The Adapter Pattern is your tool to avoid rewriting systems from scratch. By designing adapters intentionally, you:
1. **Reduce friction** between new and old code.
2. **Preserve investments** in legacy systems.
3. **Keep your architecture flexible** for future changes.

**Remember**: Adapters aren’t magic—treat them like translations. They work best when you’re explicit about what’s being transformed and why. Start small (e.g., adapt just one third-party API), measure the impact, and iterate.

Now go forth and make your incompatible interfaces collaborate—one adapter at a time.

---
### Further Reading
- [Refactoring.guru: Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
- *Clean Code* by Robert C. Martin (Chapter 6: Objects and Data Structures)
- [API Gateway vs. Adapter Pattern](https://blog.logrocket.com/api-gateway-vs-adapter-pattern/) (for microservices context)
```