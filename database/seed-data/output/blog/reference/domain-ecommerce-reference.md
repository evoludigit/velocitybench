# **[Pattern] Ecommerce Domain Patterns Reference Guide**

---

## **Overview**
The **Ecommerce Domain Patterns** reference guide provides a structured approach to modeling, querying, and implementing core ecommerce business logic. This document covers essential patterns for managing products, orders, inventory, pricing, and user interactions while ensuring scalability, maintainability, and compliance with ecommerce best practices. It focuses on domain-driven design (DDD) principles, ensuring clarity between business rules and technical implementation.

This guide is ideal for developers, architects, and analysts working on ecommerce platforms, marketplaces, or digital storefronts. It outlines key entities, their relationships, and best practices for common operations like product catalog management, order processing, and payment workflows.

---

## **Schema Reference**

### **1. Core Entities & Relationships**

| **Entity**          | **Description**                                                                                     | **Key Attributes**                                                                                     | **Relationships**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Product**         | A product sold in the store (physical or digital).                                                   | `id`, `name`, `description`, `sku`, `basePrice`, `currentPrice`, `isActive`, `taxCategoryId`           | **1:N** → `ProductVariant`, **1:1** → `ProductImage`, **1:1** → `ProductTaxCategory`              |
| **ProductVariant**  | A variation of a product (e.g., size, color).                                                      | `id`, `productId`, `sku`, `priceAdjustment`, `stockQuantity`, `isActive`, `attributes`                | **N:1** → `Product`, **1:N** → `ProductInventory`                                                   |
| **Order**           | A customer purchase containing items, status, and metadata.                                         | `id`, `userId`, `orderDate`, `status` (e.g., `PENDING`, `PROCESSING`, `SHIPPED`, `CANCELLED`), `totalAmount`, `currency`, `shippingAddress`, `paymentStatus` | **1:N** → `OrderItem`, **1:1** → `OrderShipping`, **1:1** → `OrderPayment`                         |
| **OrderItem**       | An item in an order (linked to a product variant).                                                  | `id`, `orderId`, `productVariantId`, `quantity`, `unitPrice`, `totalPrice`, `discountApplied`         | **N:1** → `Order`, **1:1** → `ProductVariant`                                                       |
| **OrderShipping**   | Shipping details and carrier information for an order.                                              | `id`, `orderId`, `carrier`, `trackingNumber`, `estimatedDelivery`, `shippingMethod`, `cost`            | **1:1** → `Order`                                                                                   |
| **OrderPayment**    | Payment details for an order (e.g., method, status, transaction ID).                               | `id`, `orderId`, `amount`, `paymentMethod`, `status` (e.g., `PENDING`, `COMPLETED`, `FAILED`), `transactionId` | **1:1** → `Order`                                                                                   |
| **Inventory**       | Tracks stock levels for product variants.                                                           | `id`, `productVariantId`, `currentStock`, `lowStockThreshold`, `lastRestockDate`                     | **1:1** → `ProductVariant`                                                                        |
| **Customer**        | User account with purchasing history.                                                                | `id`, `email`, `name`, `addresses`, `createdAt`, `lastOrderDate`                                    | **1:N** → `Order`, **1:N** → `CustomerAddress`                                                     |
| **CustomerAddress**| A shipping/billing address for a customer.                                                         | `id`, `customerId`, `type` (e.g., `SHIPPING`, `BILLING`), `street`, `city`, `state`, `postalCode`, `country` | **N:1** → `Customer`                                                                               |
| **Discount**        | A pricing promotion (e.g., percentage, fixed amount).                                              | `id`, `name`, `description`, `type` (e.g., `PERCENTAGE`, `FIXED`), `value`, `startDate`, `endDate`, `code` | **1:N** → `DiscountApplication`                                                                 |
| **DiscountApplication** | Applies a discount to an order or order item.                                                      | `id`, `discountId`, `orderId`, `orderItemId`, `appliedAmount`, `appliedAt`                          | **1:N** → `Discount`, **N:1** → `Order` or `OrderItem`                                             |
| **Review**          | Customer feedback on a product.                                                                    | `id`, `productId`, `customerId`, `rating` (1-5), `comment`, `createdAt`                             | **N:1** → `Product`, **1:1** → `Customer`                                                           |
| **Event**           | Domain events for asynchronously updating state (e.g., order status changes).                       | `id`, `eventType`, `payload`, `occurredAt`, `isProcessed`                                            | –                                                                                                    |

---

### **2. Supporting Entities**

| **Entity**          | **Description**                                                                                     | **Key Attributes**                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **PaymentMethod**   | Valid payment options (e.g., `CREDIT_CARD`, `PAYPAL`, `BANK_TRANSFER`).                             | `id`, `name`, `type`, `isActive`                                                                     |
| **ShippingMethod**  | Available shipping carriers and options.                                                              | `id`, `name`, `deliveryTime`, `cost`, `isActive`                                                      |
| **Currency**        | Supported currencies for transactions.                                                                | `id`, `code` (e.g., `USD`, `EUR`), `symbol`, `conversionRate`                                         |
| **TaxCategory**     | Tax classification for products.                                                                    | `id`, `name`, `taxRate`, `isTaxable`                                                                 |
| **ReturnRequest**   | Customer-initiated return or refund process.                                                         | `id`, `orderItemId`, `status` (e.g., `PENDING`, `APPROVED`, `RETURNED`), `reason`, `returnDate`       |

---

## **Query Examples**

### **1. Retrieving Product Catalog**
```graphql
# Fetch active products with variants and images (limit 50)
query GetProducts {
  products(limit: 50, filter: { isActive: true }) {
    id
    name
    sku
    basePrice
    currentPrice
    variants {
      sku
      priceAdjustment
      stockQuantity
      attributes
    }
    images {
      url
      altText
    }
  }
}
```

### **2. Order Processing Workflow**
#### **a) Create an Order**
```graphql
mutation CreateOrder($input: CreateOrderInput!) {
  createOrder(input: $input) {
    id
    status
    totalAmount
    payment {
      status
      transactionId
    }
    orderItems {
      productVariant {
        name
        sku
      }
      quantity
      totalPrice
    }
  }
}
```
**Input Variables (`$input`):**
```json
{
  "userId": "cust_123",
  "orderItems": [
    { "productVariantId": "var_456", "quantity": 2 },
    { "productVariantId": "var_789", "quantity": 1 }
  ],
  "shippingAddress": { "street": "123 Main St", "city": "New York" },
  "paymentMethod": "CREDIT_CARD",
  "paymentDetails": { "cardLast4": "4242" }
}
```

#### **b) Update Order Status (Using Domain Events)**
```graphql
# Simulate order payment completion (emits `OrderPaid` event)
mutation UpdateOrderStatus($orderId: ID!, $status: OrderStatus!) {
  updateOrderStatus(input: { orderId: $orderId, status: $status }) {
    status
    updatedAt
  }
}
```

#### **c) Fetch Order History for a Customer**
```graphql
query GetCustomerOrders($userId: ID!) {
  orders(filter: { userId: $userId }, sort: { field: orderDate, order: DESC }) {
    id
    orderDate
    status
    totalAmount
    shipping {
      trackingNumber
      estimatedDelivery
    }
    payment {
      status
      paymentMethod
    }
  }
}
```

### **3. Inventory Management**
```graphql
# Check stock levels for variants
query CheckInventory {
  productVariants(limit: 10) {
    id
    sku
    stockQuantity
    lowStockThreshold
    product {
      name
    }
  }
}

# Reserve inventory for an order (optimistic locking)
mutation ReserveInventory($items: [ReserveInventoryInput!]!) {
  reserveInventory(items: $items) {
    success
    messages
  }
}
```
**Input Variables (`$items`):**
```json
[
  { "productVariantId": "var_456", "quantity": 2 },
  { "productVariantId": "var_789", "quantity": 1 }
]
```

### **4. Discount Application**
```graphql
# Apply a discount code to an order
mutation ApplyDiscount($orderId: ID!, $code: String!) {
  applyDiscount(input: { orderId: $orderId, code: $code }) {
    discountApplied
    newTotalAmount
    discount {
      name
      value
    }
  }
}
```

### **5. Review Management**
```graphql
# Submit a product review
mutation SubmitReview($input: CreateReviewInput!) {
  createReview(input: $input) {
    id
    rating
    comment
    product {
      name
    }
  }
}
```
**Input Variables (`$input`):**
```json
{
  "productId": "prod_101",
  "customerId": "cust_789",
  "rating": 5,
  "comment": "Great product!"
}
```

---

## **Best Practices**

### **1. Data Model Design**
- **Normalize for Queries**: Avoid over-normalization that complicates reads (e.g., denormalize `OrderItem` for performance).
- **Use Enums for Statuses**: Standardize order/payment statuses (e.g., `OrderStatus: Pending | Processing | Shipped | Cancelled`).
- **Composite Keys for Inventory**: Combine `productVariantId` + `warehouseId` if multi-location inventory exists.

### **2. Transactions**
- **Atomic Order Creation**: Use distributed transactions (Saga pattern) or two-phase commit for order + payment.
- **Inventory Locking**: Implement optimistic/pessimistic locking to prevent overselling (e.g., `RESERVED` inventory state).

### **3. Performance**
- **Caching**: Cache product catalogs, pricing, and order totals (e.g., Redis).
- **Pagination**: Limit `products`, `orders`, and `reviews` to 25–100 items per page.
- **Lazy Loading**: Load `ProductImages` and `OrderShipping` only when needed.

### **4. Security**
- **Input Validation**: Sanitize `discountCode` and `paymentDetails` to prevent misuse.
- **Authorization**: Restrict `Order` writes to the customer or admin.
- **Audit Logs**: Track changes to `ProductPrice`, `OrderStatus`, and `Inventory`.

### **5. Extensibility**
- **Event-Driven Architecture**: Use domain events (e.g., `OrderCreated`, `PaymentFailed`) for async workflows.
- **Plugin System**: Design for third-party integrations (e.g., shipping carriers, payment gateways).

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| **Price inconsistency**               | Use events to sync prices across services (e.g., `PriceUpdated` event).                          |
| **Race conditions in inventory**      | Implement inventory reservations with TTL (time-to-live) or retries.                              |
| **Discount conflicts**                | Prioritize discounts (e.g., percentage over fixed) and validate eligibility at checkout.         |
| **Slow product searches**             | Use full-text search (Elasticsearch) for `Product.name` and `Product.description`.              |
| **Cart abandonment**                  | Send `CartSaved` events to trigger recovery emails with discounts.                                 |
| **Tax calculation errors**            | Centralize tax rules in a `TaxService` with caching.                                               |

---

## **Related Patterns**

1. **Order Management System (OMS)**
   - Extends this pattern with advanced features like **subscription models**, **recurring payments**, or **order fulfillment automation**.
   - *See*: [OMS Pattern Guide](link).

2. **Product Catalog Management**
   - Focuses on **multi-variant products**, **attribute hierarchies**, and **dynamic pricing engines**.
   - *See*: [Catalog Pattern Guide](link).

3. **Payment Processing**
   - Covers **fraud detection**, **retries**, and **multi-currency support**.
   - *See*: [Payment Pattern Guide](link).

4. **Inventory Optimization**
   - Includes **forecasting**, **auto-replenishment**, and **last-mile logistics**.
   - *See*: [Inventory Pattern Guide](link).

5. **Checkout Optimization**
   - Reduces abandonment with **guest checkout**, **one-click payments**, and **progress indicators**.
   - *See*: [Checkout Pattern Guide](link).

6. **Personalization & Recommendations**
   - Uses **collaborative filtering** or **rule-based systems** to suggest products.
   - *See*: [Personalization Pattern Guide](link).

7. **Returns & Refunds**
   - Standardizes **return policies**, **partial refunds**, and **damage handling**.
   - *See*: [Returns Pattern Guide](link).

---

## **Further Reading**
- **Domain-Driven Design (DDD)**: *EventStorming* for ecommerce workflows.
- **Microservices**: Decompose by bounded contexts (e.g., `CatalogService`, `OrderService`).
- **Testing**: Mock `PaymentGateway` and `ShippingService` in unit tests.