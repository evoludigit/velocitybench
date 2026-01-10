```markdown
# **Anti-Corruption Layer: How to Safely Integrate Legacy Systems Without Compromising Your Domain**

*Protect your clean architecture from the chaos of legacy codebases—one layer at a time.*

---

## **Introduction**

As backend engineers, we’ve all faced the "legacy system" battle. That *just works* (mostly) monolith sits in the corner of our architecture, written in a mix of technologies, with inconsistent APIs, and often tying our hands when it comes to modern design principles. Worse yet, our shiny new domain models—crafted with care using DDD, CQRS, or hexagonal architecture—suddenly need to talk to this beast.

**This is where the Anti-Corruption Layer (ACL) pattern comes in.**

Introduced by **Martin Fowler** in his paper ["Patterns of Enterprise Application Architecture"](https://martinfowler.com/eaaCatalog/antiCorruptionLayer.html), the Anti-Corruption Layer is a defensive shield around your domain. It bridges the gap between your clean architecture and legacy systems, ensuring that external constraints don’t seep into your core logic. But unlike a firewall, it’s not just about security—it’s about **decoupling, isolation, and controlled data transformation**.

In this post, we’ll explore:
- Why legacy systems are a ticking time bomb for your architecture.
- How the Anti-Corruption Layer solves this problem in practice.
- Real-world implementations with code examples.
- Pitfalls to avoid and best practices to follow.

---

## **The Problem: Legacy Systems as Architecture Hurdles**

Legacy systems are inevitable in enterprise applications. They often represent:
- **Historical debt**: Built when technologies like SOAP, stored procedures, or flat-file databases were the norm.
- **Unpredictable APIs**: Poorly documented, versioned inconsistently, or coupled with business logic.
- **Tight coupling**: Your domain models might need to interact with these systems directly, forcing you to conform to their quirks rather than designing your own clean interfaces.

### **Example Scenario: The E-Commerce Checkout**
Imagine an e-commerce platform with a modern **Order Service** (built with DDD) and a legacy **Inventory Management System** exposed via a SOAP web service. The legacy system:
- Uses a non-standard `SKU` format (e.g., `"PROD-123-A"` vs. your domain’s `ProductId` UUID).
- Requires all inventory checks to be made in a single transaction.
- Throws cryptic errors like `"INV-9999"`.

If you connect your domain directly to this system, you risk:
1. **Polluting your domain**: Your `Order` entity might inherit the legacy `SKU` format, forcing you to manage both formats.
2. **Fragile design**: A small change in the legacy API (e.g., adding a new field) could break your domain logic.
3. **Technical debt**: You’ll spend more time mapping data than writing business rules.

This is where the Anti-Corruption Layer steps in.

---

## **The Solution: The Anti-Corruption Layer**

The Anti-Corruption Layer (ACL) acts as a **translation buffer** between your domain and external systems. Its primary goals are:
1. **Isolate your domain** from external constraints.
2. **Provide a stable, well-defined API** for your domain to interact with the legacy system.
3. **Handle all data transformations** in one place, keeping your domain pure.

### **How It Works**
The ACL typically consists of:
1. **A public interface** (e.g., a service or repository) that your domain uses.
2. **A private implementation** that handles the messy details of the legacy system.
3. **Data mappers** to convert between your domain objects and the legacy system’s data models.

---

## **Components of the Anti-Corruption Layer**

### **1. The Public Interface**
This is the clean, domain-friendly API that your application’s services and repositories use. It abstracts away the legacy system’s details.

**Example: Order Service Interface**
```typescript
// src/domain/order-service.ts
interface IOrderService {
  createOrder(orderData: OrderCreateDto): Promise<Order>;
  checkInventory(productId: string): Promise<boolean>;
}
```

### **2. The Private Implementation**
This layer implements the public interface but delegates to the legacy system. It handles all the ugly work.

**Example: SOAP-Based Implementation**
```typescript
// src/infrastructure/order-service-soap.ts
import { IOrderService } from '../domain/order-service';
import { LegacyInventoryAPI } from './legacy-inventory-api';

export class OrderServiceSoap implements IOrderService {
  private readonly legacyApi: LegacyInventoryAPI;

  constructor(legacyApi: LegacyInventoryAPI) {
    this.legacyApi = legacyApi;
  }

  async createOrder(orderData: OrderCreateDto): Promise<Order> {
    // Transform domain data to legacy format
    const legacyOrder = this.toLegacyOrder(orderData);
    const response = await this.legacyApi.submitOrder(legacyOrder);

    // Transform legacy response to domain
    return this.toDomainOrder(response);
  }

  async checkInventory(productId: string): Promise<boolean> {
    // Legacy system expects SKU, not UUID
    const sku = this.convertProductIdToSku(productId);
    const result = await this.legacyApi.checkStock(sku);
    return result.available;
  }

  private toLegacyOrder(orderData: OrderCreateDto): LegacyOrderDto {
    return {
      orderId: orderData.id,
      items: orderData.items.map(item => ({
        sku: this.convertProductIdToSku(item.productId),
        quantity: item.quantity,
      })),
    };
  }

  private convertProductIdToSku(productId: string): string {
    // Business logic to map UUID to legacy SKU format
    return `PROD-${productId.split('-')[1]}-A`;
  }
}
```

### **3. Data Mappers**
These classes handle the conversion between your domain objects and the legacy system’s data models. They keep your domain logic clean and focused.

**Example: Legacy Inventory API Wrapper**
```typescript
// src/infrastructure/legacy-inventory-api.ts
export class LegacyInventoryAPI {
  private readonly soapClient: any; // Hypothetical SOAP client

  async checkStock(sku: string): Promise<LegacyStockResponse> {
    const response = await this.soapClient.call({
      method: 'CheckStock',
      params: { sku },
    });
    return response.stock;
  }
}
```

---

## **Implementation Guide**

### **Step 1: Define Your Public Interface**
Start by designing the interface your domain will use. Keep it **simple and domain-oriented**.

**Example: Repository Pattern**
```typescript
// src/domain/product-repository.ts
interface ProductRepository {
  findById(id: string): Promise<Product>;
  save(product: Product): Promise<void>;
}
```

### **Step 2: Implement the ACL Layer**
Create a private implementation that maps to the legacy system. Use **dependency injection** to swap implementations later if needed.

**Example: SQL Database vs. SOAP Layer**
```typescript
// src/infrastructure/product-repository-legacy.ts
import { ProductRepository } from '../domain/product-repository';
import { LegacyDatabaseClient } from './legacy-database-client';

export class LegacyProductRepository implements ProductRepository {
  constructor(private readonly dbClient: LegacyDatabaseClient) {}

  async findById(id: string): Promise<Product> {
    // Legacy DB uses a different ID format
    const legacyId = this.convertId(id);
    const rawData = await this.dbClient.query(
      `SELECT * FROM PRODUCTS WHERE ID = ?`,
      [legacyId]
    );

    return this.toDomainProduct(rawData);
  }

  private convertId(id: string): string {
    // Convert UUID to legacy format
    return `LEGACY_${id.replace(/-/g, '')}`;
  }
}
```

### **Step 3: Use Dependency Injection**
Inject the ACL implementation into your domain services.

**Example: Order Service Composition**
```typescript
// src/application/order-service.ts
import { IOrderService } from '../domain/order-service';
import { OrderServiceSoap } from '../infrastructure/order-service-soap';
import { LegacyInventoryAPI } from '../infrastructure/legacy-inventory-api';

export class OrderService {
  constructor(private readonly orderService: IOrderService) {}

  async placeOrder(orderData: OrderCreateDto): Promise<Order> {
    const order = await this.orderService.createOrder(orderData);
    // Business logic here...
    return order;
  }
}

// Wire up the dependency in your entry point
const legacyApi = new LegacyInventoryAPI();
const orderService = new OrderServiceSoap(legacyApi);
const orderServiceApp = new OrderService(orderService);
```

### **Step 4: Test the ACL Layer**
Write tests to ensure your mappings are correct and edges cases are handled.

**Example: Unit Test for Data Conversion**
```typescript
// src/infrastructure/order-service-soap.test.ts
import { OrderServiceSoap } from './order-service-soap';
import { LegacyInventoryAPI } from './legacy-inventory-api';

jest.mock('./legacy-inventory-api');

describe('OrderServiceSoap', () => {
  it('should convert product IDs correctly', async () => {
    const mockLegacyApi = new LegacyInventoryAPI() as jest.Mocked<LegacyInventoryAPI>;
    const service = new OrderServiceSoap(mockLegacyApi);

    const result = await service.checkInventory('123e4567-e89b-12d3-a456-426614174000');
    expect(mockLegacyApi.checkStock).toHaveBeenCalledWith('PROD-89B-12D3A456-A');
  });
});
```

---

## **Common Mistakes to Avoid**

### **1. Exposing Legacy Details in Your Domain**
❌ **Bad**: Your `Order` entity includes a `sku` field to match the legacy system.
✅ **Good**: Use the ACL to translate only what’s necessary for domain logic.

### **2. Ignoring Error Handling**
Legacy systems often throw vague errors. Don’t let them bubble up to your domain.

```typescript
// Bad: Pass through legacy errors
try {
  await legacyApi.call();
} catch (error) {
  throw error; // Oops, now your domain sees "INV-9999"
}

// Good: Translate to domain-specific errors
catch (error) {
  if (error.code === 'INV-9999') {
    throw new InventoryUnavailableError('Product out of stock');
  }
  throw new LegacySystemError(error);
}
```

### **3. Overcomplicating the ACL**
If your ACL becomes as complex as the legacy system, you’re doing it wrong. Keep it focused on **one responsibility**: translation.

### **4. Not Testing Edge Cases**
Legacy systems often have quirky behaviors (e.g., case-sensitive IDs, null handling). Test these scenarios rigorously.

---

## **Key Takeaways**

✅ **Isolate your domain** from legacy constraints using the ACL.
✅ **Keep the public interface clean**—hide legacy details behind abstractions.
✅ **Use data mappers** to handle all translations in one place.
✅ **Test the ACL thoroughly**, especially edge cases.
✅ **Avoid tight coupling**—design your ACL to be replaceable.
✅ **Document the ACL’s purpose** so future developers understand why it exists.

---

## **Conclusion**

The Anti-Corruption Layer is a **practical, battle-tested pattern** for managing legacy system integration without sacrificing clean architecture. By treating the ACL as a **defensive buffer**, you protect your domain from the chaos of external systems while keeping your codebase maintainable and flexible.

### **When to Use It**
- You have a legacy system you must integrate with.
- Your domain would be polluted by legacy constraints.
- You want to avoid direct coupling between your application and external APIs.

### **When Not to Use It**
- The legacy system is trivial (e.g., a simple REST API with no quirks).
- Your team is willing to refactor the legacy system entirely.

### **Final Thought**
The ACL isn’t about avoiding legacy systems—it’s about **managing the pain points** they introduce. By applying this pattern, you can breathe new life into your architecture while keeping your domain models pristine.

Now go forth and defend your codebase!

---
**Further Reading:**
- [Martin Fowler’s Anti-Corruption Layer](https://martinfowler.com/eaaCatalog/antiCorruptionLayer.html)
- [Hexagonal Architecture (Ports and Adapters)](https://alistair.cockburn.us/hexagonal-architecture/)
- ["Working Effectively with Legacy Code" by Michael Feathers](https://www.amazon.com/Working-Effectively-Legacy-Michael-Feathers/dp/0131177052)

---
*What’s your most painful legacy system integration? Share your stories in the comments!*
```