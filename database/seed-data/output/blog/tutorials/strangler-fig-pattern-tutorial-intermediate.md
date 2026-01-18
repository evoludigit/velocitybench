```markdown
---
title: "The Strangler Fig Pattern: How to Migrate Monoliths Without Ripping and Replacing"
date: "2023-10-15"
author: "Alex Chen, Senior Backend Engineer"
description: "Learn how to incrementally replace monolithic services with microservices using the Strangler Fig Pattern. Practical examples, tradeoffs, and implementation tips."
tags: ["backend", "microservices", "refactoring", "migration", "patterns"]
---

# The Strangler Fig Pattern: How to Migrate Monoliths Without Ripping and Replacing

You’re running a monolith. It’s fast, but it’s also bloated, hard to scale, and slowing down your team. You’ve heard microservices can solve these problems—but replacing the entire monolith at once seems scary. The good news? You don’t have to. The **Strangler Fig Pattern** lets you migrate incrementally, replacing parts of your monolith one feature or service at a time. Think of it like a garden: instead of uprooting the fig tree (your monolith), you slowly replace its branches (services) with healthier alternatives.

In this guide, I’ll walk you through what the Strangler Fig Pattern is, why it’s useful, how to implement it, and what to watch out for. We’ll cover real-world examples in code, tradeoffs, and best practices to make your migration smoother.

---

## The Problem: Why Monoliths Are Hard to Change

Monoliths are simple, but they come with downsides. As your application grows, so does the monolith’s complexity. Here’s what happens when you try to change it:

1. **Deployment Complexity**: Every change requires a full redeploy, slowing down feedback loops. A single bug can break the entire application.
2. **Team Bottlenecks**: Only a few engineers can safely modify the monolith because of its tight coupling. New hires take months to understand the codebase.
3. **Scaling Pain**: If one feature scales poorly, the whole app suffers because everything is in one process.
4. **Technical Debt**: Adding new functionality becomes harder over time, leading to rushed fixes or workarounds.

A common reaction is to replace the entire monolith at once. But this is risky:
- **Downtime**: You can’t stop serving users while you rewrite everything.
- **Cost**: Hiring a large team to build a new system from scratch is expensive.
- **Uncertainty**: You might discover new requirements midway, forcing you to pivot.

The Strangler Fig Pattern solves this by letting you **replace parts of the monolith gradually**, reducing risk while delivering value incrementally.

---

## The Solution: Strangler Fig Pattern

The Strangler Fig Pattern is a **strategy for migrating away from a monolith** by slowly replacing one piece at a time. The name comes from the way fig trees grow: new shoots (your microservices) strangle and replace the old tree (the monolith). Here’s how it works:

1. **Identify a feature or module** in the monolith that can be replaced.
2. **Build a new service** (microservice, API, or standalone app) that handles this feature.
3. **Make the new service live alongside the monolith**, routing traffic to either the old or new implementation.
4. **Gradually shift traffic** from the monolith to the new service.
5. **Repeat** for other features until the monolith is no longer needed.

### Why This Works
- **Low Risk**: You’re never replacing the entire system all at once.
- **Flexibility**: You can pivot if the new service doesn’t work as expected.
- **Incremental Value**: You deliver new features or improvements early.
- **Technical Debt Control**: You address high-impact areas first.

---

## Components of the Strangler Fig Pattern

To implement this pattern, you’ll need a few key components:

1. **Feature Toggles**: Allow you to enable/disable the new service for specific users or traffic.
2. **API Gateways**: Route requests to either the monolith or the new service.
3. **Data Migration Strategies**: Handle data transfer from the monolith to the new service.
4. **Monitoring and Observability**: Track performance and errors in both systems.
5. **CI/CD Pipelines**: Ensure the new services can be deployed independently.

---

## Code Examples: Implementing Strangler Fig

Let’s walk through a practical example. Suppose we have a monolithic e-commerce backend with these features:
- **User Management** (auth, profiles)
- **Product Catalog** (CRUD for products)
- **Orders** (checkout, processing)

We’ll start by replacing the **Product Catalog** with a new microservice.

### 1. Monolith API (Before Migration)
Here’s a simplified version of the monolith’s product-related endpoints:

```java
@RestController
public class ProductController {
    @Autowired
    private ProductService productService;

    @GetMapping("/products")
    public List<Product> getProducts() {
        return productService.getAllProducts();
    }

    @PostMapping("/products")
    public Product createProduct(@RequestBody Product product) {
        return productService.createProduct(product);
    }
}
```

### 2. New Microservice (Product Service)
We’ll build a standalone microservice for products. Let’s use Spring Boot for consistency:

**`ProductServiceApplication.java`**
```java
@SpringBootApplication
public class ProductServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(ProductServiceApplication.class, args);
    }
}
```

**`ProductController.java` (New Service)**
```java
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @Autowired
    private ProductRepository productRepository;

    @GetMapping
    public List<Product> getProducts() {
        return productRepository.findAll();
    }

    @PostMapping
    public Product createProduct(@RequestBody Product product) {
        return productRepository.save(product);
    }
}
```

### 3. API Gateway (Routing Traffic)
We’ll use **Spring Cloud Gateway** to route traffic between the monolith and the new service. Here’s how we configure it:

```yaml
# application.yml
spring:
  cloud:
    gateway:
      routes:
        - id: monolith_products
          uri: http://monolith:8080
          predicates:
            - Path=/legacy/products
          filters:
            - RewritePath=/legacy/products, /products
        - id: new_product_service
          uri: http://product-service:8080
          predicates:
            - Path=/api/products
```

### 4. Feature Toggle (Example: Canary Deployment)
We’ll use a feature flag to gradually roll out the new service. Let’s add this to the gateway or monolith:

```java
// In the gateway or monolith's ProductController
@GetMapping("/products")
public ResponseEntity<Object> getProducts(@RequestHeader(value = "X-User-Type", defaultValue = "user") String userType) {
    if (userType.equals("premium") && isNewServiceEnabled()) {
        return gatewayProxy.get("/api/products");
    } else {
        return ResponseEntity.ok(productService.getAllProducts());
    }
}

private boolean isNewServiceEnabled() {
    // Check environment or feature flag service
    return System.getenv("ENABLE_NEW_PRODUCT_SERVICE") != null;
}
```

### 5. Data Migration (Example: Syncing Data)
Initially, the new service will read from the monolith’s database. Over time, you’ll migrate data incrementally:

```java
// In the new ProductService's start-up
@PostConstruct
public void initializeData() {
    Optional<Integer> count = productRepository.count();
    if (count.isEmpty()) {
        // Sync data from monolith
        List<Product> productsFromMonolith = restTemplate.getForObject(
            "http://monolith:8080/products",
            List.class
        );
        productRepository.saveAll(productsFromMonolith);
    }
}
```

---

## Implementation Guide

### Step 1: Choose the Right Feature to Replace
- **Start with low-risk features**: Look for modules that:
  - Are rarely changed.
  - Have clear boundaries.
  - Don’t tightly couple with other features.
- **Example**: A product catalog is a good candidate, while user authentication might be riskier.

### Step 2: Build the New Service Independently
- **Avoid tight coupling**: The new service should not depend on the monolith’s database or internals.
- **Use APIs**: Communicate via REST, gRPC, or event-driven architectures.
- **Example**: If the monolith uses SQL, the new service might use PostgreSQL or MongoDB.

### Step 3: Deploy the New Service Side-by-Side
- **Use containers**: Docker and Kubernetes make it easier to deploy new services alongside the monolith.
- **Feature flags**: Allow A/B testing or gradual rollout.

### Step 4: Route Traffic Gradually
- **Start with a small percentage of traffic** (e.g., 10% of users).
- **Monitor errors and performance**: Use tools like Prometheus, Grafana, or cloud-native observability.
- **Example**: Use a service mesh (like Istio) to manage traffic splitting.

### Step 5: Migrate Data
- **Initial sync**: Copy all existing data to the new service.
- **Delta updates**: Use change data capture (CDC) tools like Debezium to sync future changes.
- **Fade out the monolith**: Once the new service is stable, reduce reads from the monolith.

### Step 6: Remove the Monolith
- **Phase out the old endpoints**: Redirect all traffic to the new service.
- **Update client apps**: Ensure all consumers use the new API.
- **Archive old data**: If needed, keep a read-only copy of the monolith’s data.

---

## Common Mistakes to Avoid

1. **Skipping Feature Flags**
   - Without feature flags, you can’t safely roll out the new service. Always enable/disable it at runtime.

2. **Ignoring Data Migration**
   - Don’t assume the new service can read from the monolith’s database indefinitely. Plan for a complete migration.

3. **Overcomplicating the API Gateway**
   - Start simple. You can add more sophisticated routing (e.g., canary releases) later.

4. **Not Monitoring the Transition**
   - Use observability tools to track errors, latency, and traffic shifts. Without monitoring, you won’t catch issues early.

5. **Replacing Everything at Once**
   - The Strangler Fig Pattern is about **incremental change**. Don’t try to replace the entire monolith in one go.

6. **Neglecting Backward Compatibility**
   - Ensure the new service can accept requests in the old format, at least temporarily.

---

## Key Takeaways
Here’s what you should remember:

- **Incremental Change**: Replace one feature or module at a time to reduce risk.
- **Side-by-Side Deployment**: Keep the old and new systems running together during the transition.
- **Feature Flags**: Enable gradual rollout and rollback if needed.
- **Data Migration**: Plan for initial sync and ongoing updates.
- **Observability**: Monitor both systems to catch issues early.
- **Start Small**: Begin with low-risk features to build confidence.
- **No Silver Bullet**: The Strangler Fig Pattern isn’t magic. It requires discipline and planning.

---

## Conclusion

The Strangler Fig Pattern is a practical way to migrate from a monolith to microservices without the risk of a big-bang rewrite. By replacing one piece at a time, you can deliver value incrementally, reduce technical debt, and adapt to changing requirements.

Remember:
- **Start small** and focus on low-risk features.
- **Use feature flags** to control the rollout.
- **Monitor everything** to ensure a smooth transition.
- **Keep learning**—each migration will teach you how to do the next one better.

If you’re stuck with a monolith, the Strangler Fig Pattern is your roadmap to modern, scalable architecture—one branch at a time. Happy migrating!

---
```