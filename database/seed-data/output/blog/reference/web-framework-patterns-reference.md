# **[Web Framework Patterns] Reference Guide**

---

## **Overview**
Web framework patterns define reusable architectures and best practices for organizing, routing, and processing HTTP requests efficiently. These patterns, including **Middleware**, **Routing**, **Controller**, **View**, and **Service**, simplify server-side logic, enhance modularity, and improve maintainability. By leveraging these patterns, developers can abstract common concerns (e.g., authentication, logging) into reusable components, reduce code duplication, and align with established web conventions. This reference guide outlines core concepts, implementation strategies, and optimization techniques for integrating web framework patterns into modern applications.

---

## **Schema Reference**

| **Pattern**       | **Purpose**                                                                                  | **Key Components**                                                                                     | **Lifespan**                                                                                     |
|-------------------|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Middleware**    | Process HTTP requests/responses before/after controller execution (e.g., auth, logging). | Functions or classes (e.g., `express.js` middleware, `Django` middleware).                          | Runs globally or per route.                                                                     |
| **Routing**       | Maps URLs to handler functions (controllers).                                               | Route objects, path parameters, HTTP methods (GET/POST).                                             | Persists per application or module.                                                              |
| **Controller**    | Handles request logic and delegates to services/views.                                     | Functions or classes (e.g., `ASP.NET` controllers, `Spring MVC` handlers).                           | Short-lived per request.                                                                      |
| **View**          | Renders dynamic content (e.g., HTML, JSON APIs) using templates or frameworks.             | Templates (Jinja2, Handlebars), rendering engines (e.g., `EJS`, `Thymeleaf`).                         | Instantiated per request.                                                                    |
| **Service**       | Encapsulates business logic independent of frameworks.                                      | Domain-specific classes/functions (e.g., `UserService`, `OrderService`).                              | Long-lived (singleton or per-request).                                                        |
| **Dependency Injection (DI)** | Manages object dependencies (e.g., injecting services into controllers).               | DI containers (e.g., `IoC`, `Guice`, `Spring`).                                                       | Runtime-managed (centralized or framework-provided).                                           |

---

## **Pattern Implementations**

### **1. Middleware**
Middleware processes requests/responses sequentially. Example in **Node.js (Express):**
```javascript
// Authentication middleware
app.use((req, res, next) => {
  if (!req.headers.authorization) return res.status(401).send("Unauthorized");
  next();
});
```
**Best Practices:**
- Chain middleware with `app.use()` or route-specific handlers.
- Avoid overly complex middleware (split into small, reusable functions).
- Log errors explicitly to prevent silent failures.

**Optimization:**
- Use `app.use(express.json())` for automatic JSON parsing.
- Leverage `express-rate-limit` to mitigate brute-force attacks.

---

### **2. Routing**
Routes define how URLs map to handler functions. Example in **Python (Flask):**
```python
from flask import Flask
app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return {"id": user_id}
```
**Key Features:**
- **Dynamic Segments:** Capture path variables (e.g., `/users/:id`).
- **HTTP Methods:** Explicitly declare `GET`, `POST`, etc.
- **Route Groups:** Organize routes with shared prefixes (e.g., `/api/v1`).

**Optimization:**
- Use **regex patterns** for advanced URL matching.
- Cache route lookup results (e.g., `express-route-cache`).

---

### **3. Controller**
Controllers act as intermediaries between routes and services. Example in **Go (Gin):**
```go
type UserController struct {
    userService *UserService
}

func (c *UserController) GetUser(ctx *gin.Context) {
    user := c.userService.Get(ctx.Param("id"))
    ctx.JSON(200, user)
}
```
**Best Practices:**
- **Separation of Concerns:** Keep controllers thin (delegate logic to services).
- **Request/Response Handling:** Validate inputs/outputs explicitly.
- **Error Handling:** Use wrappers (e.g., `http.Error` in Go) for consistent errors.

**Optimization:**
- Use **structs** for request/response DTOs (e.g., `struct{ Id string }`).
- Reuse controllers via dependency injection.

---

### **4. View**
Views render dynamic content. Example in **PHP (Laravel Blade):**
```html
<!-- resources/views/user.blade.php -->
<h1>User: @{{ $user->name }}</h1>
```
**Key Frameworks:**
- **Jinja2 (Python):** `{{ variable }}` templating.
- **EJS (Node.js):** `<%- variable %>` syntax.
- **Thymeleaf (Java):** `<span th:text="${variable}">`.

**Optimization:**
- **Partial Rendering:** Use includes (e.g., `<partial name="header">`).
- **Caching:** Enable template caching (e.g., `ejs.cache`).

---

### **5. Service Layer**
Services encapsulate business logic. Example in **Java (Spring):**
```java
@Service
public class UserService {
    public User getUser(String id) {
        return userRepository.findById(id).orElseThrow();
    }
}
```
**Best Practices:**
- **Unit of Work:** Services manage transactions (e.g., `@Transactional` in Spring).
- **Repository Pattern:** Abstract data access (e.g., `UserRepository`).
- **Domain Logic:** Keep services focused (e.g., `OrderService`, `PaymentService`).

**Optimization:**
- **Caching:** Use `@Cacheable` (Spring) or `redis` for frequently accessed data.
- **Asynchronous Processing:** Offload tasks (e.g., `Task` in Spring).

---

### **6. Dependency Injection (DI)**
DI decouples dependencies. Example in **TypeScript (InversifyJS):**
```typescript
const container = new Container();
container.bind(UserService).to(UserServiceImpl);
container.bind(UserController).to(UserControllerImpl);
```
**Frameworks:**
- **IoC Containers:** `Guice` (Java), `Dagger` (Android).
- **Manual DI:** Constructor injection (recommended).

**Optimization:**
- **Lazy Initialization:** Load dependencies only when needed.
- **Scopes:** Define lifetimes (e.g., singleton for services).

---

## **Query Examples**

### **Middleware Pipeline**
```bash
# Express: Log all requests
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next();
});
```

### **Dynamic Routing**
```python
# Flask: Regex-based route
app.route("/search/<regex('^[a-z]+$')>query")(search_handler)
```

### **Controller with DI**
```go
// Gin: Inject dependencies
type UserController struct {
    userRepo UserRepository
}

func NewUserController(repo UserRepository) *UserController {
    return &UserController{repo}
}
```

### **Service Method**
```java
// Spring: Cache-enabled service
@Service
public class UserService {
    @Cacheable("users")
    public User findById(String id) { ... }
}
```

---

## **Related Patterns**
1. **Layered Architecture:** Separates concerns into presentation, business, and data layers.
2. **CQRS (Command Query Responsibility Segregation):** Splits reads/writes for scalability.
3. **Event-Driven Architecture:** Uses events (e.g., Redis pub/sub) for async workflows.
4. **API Gateway:** Centralizes routing for microservices (e.g., Kong, AWS API Gateway).
5. **Circuit Breaker:** Resilient error handling (e.g., Hystrix, Resilience4j).

---

## **Antipatterns to Avoid**
- **God Middleware:** Overly complex middleware bloat.
- **Anemic Controllers:** Controllers handling business logic (violate separation of concerns).
- **Hardcoded Views:** Templates tied directly to controllers (reduce reusability).
- **Global State in Services:** Shared mutable state leads to race conditions.

---
**Reference Sources:**
- [Express.js Docs](https://expressjs.com/)
- [Flask Routing](https://flask.palletsprojects.com/en/2.0.x/quickstart/#routes-and-view-functions)
- [Spring MVC](https://docs.spring.io/spring-framework/docs/current/reference/html/web.html)
- *Domain-Driven Design* (Eric Evans) for service layer design.