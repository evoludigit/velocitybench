---

# **[Builder Pattern] Reference Guide**

---

## **Overview**
The **Builder Pattern** is a **creational design pattern** that separates the construction of a complex object from its representation, allowing the same construction process to create different representations. This pattern is particularly useful when an object requires extensive configuration, has many optional parameters, or has a nested/fluent API. By encapsulating the construction logic in a separate `Builder` class, the pattern simplifies object creation, improves readability, and reduces boilerplate code. It is widely used in **APIs, configuration builders, and DTO factories**, especially in languages like Java, Kotlin, and C#.

---

## **Schema Reference**

| **Component**               | **Responsibility**                                                                 | **Key Methods/Attributes**                                                                 | **Example Use Case**                          |
|-----------------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Product**                 | Represents the complex object being constructed.                                   | Immutable fields (e.g., `public final String value`).                                    | A `User` object with multiple required fields.|
| **Builder**                 | Encapsulates the construction logic. Maintains the state of the object being built.| Builder methods (e.g., `setField()`, `build()`), private `Product` instance.             | Building a `Report` with optional sections.   |
| **Abstract Builder** (optional) | Defines the interface for all concrete builders (useful for hierarchical builds). | Abstract methods (e.g., `abstract String setSection()`).                               | Used in frameworks like Guava’s `ListBuilder`.  |
| **Director** (optional)     | Orchestrates the construction process by defining the order of steps (useful for hierarchical builders). | Methods like `construct()`.                                                               | A `DocumentBuilder` with predefined templates. |

---

## **Implementation Details**

### **1. Basic Builder Pattern**
A minimal implementation involves:
- A **product class** with immutable fields.
- A **builder class** with setter methods and a `build()` method to return the product.

#### **Code Example (Java)**
```java
// Product
public final class User {
    private final String name;
    private final int age;
    private final String email;

    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
    }

    // Getters omitted for brevity

    // Static nested Builder class
    public static class Builder {
        private String name;
        private int age;
        private String email;

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder age(int age) {
            this.age = age;
            return this;
        }

        public Builder email(String email) {
            this.email = email;
            return this;
        }

        public User build() {
            return new User(this);
        }
    }
}
```

#### **Usage Example**
```java
User user = new User.Builder()
    .name("Alice")
    .age(30)
    .email("alice@example.com")
    .build();
```

---

### **2. Telescoping Constructor (Anti-Pattern)**
Avoid this approach:
```java
User user = new User("Alice"); // Mandatory
user.setAge(30);               // Optional
user.setEmail("alice@example.com"); // Optional
```
**Problems:** Violates **Single Responsibility Principle**, results in inconsistent states.

---

### **3. Java’s `Builder` Pattern (Immutable Objects)**
Leverage **Lombok** or ** records** for concise builders:
```java
@Builder
public record User(String name, int age, String email) {}
```
Or manually:
```java
public class User {
    private final String name;
    private final int age;
    private final String email;

    private User(String name, int age, String email) {
        this.name = name;
        this.age = age;
        this.email = email;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String name;
        private int age;
        private String email;

        public Builder name(String name) { this.name = name; return this; }
        public Builder age(int age) { this.age = age; return this; }
        public Builder email(String email) { this.email = email; return this; }

        public User build() {
            return new User(name, age, email);
        }
    }
}
```

---

### **4. Fluent API (Method Chaining)**
Ensure return types are `Builder` for method chaining:
```java
public Builder setField1(String value) {
    this.field1 = value;
    return this; // Enables chaining
}
```

---

### **5. Hierarchical Builders**
Use an **abstract builder** for complex nested structures:
```java
public abstract class PizzaBuilder {
    protected Pizza pizza;

    public Pizza build() {
        return pizza;
    }

    public abstract void buildDough();
    public abstract void buildSauce();
}

public class SpicyPizzaBuilder extends PizzaBuilder {
    @Override public void buildDough() { /* ... */ }
    @Override public void buildSauce() { /* ... */ }
}
```

---

### **6. Factory Methods vs. Builder Pattern**
| **Builder**                          | **Factory Method**                          |
|--------------------------------------|---------------------------------------------|
| Used when object construction is complex. | Used for simple object creation.           |
| Fluent API-style chaining (`builder().setX().build()`). | Static method (`Factory.create()`).       |
| Encapsulates intermediate states.   | Returns a pre-defined object type.         |

---

## **Query Examples**

### **1. Building a Complex DTO**
```java
Order order = new Order.Builder()
    .customerId("C123")
    .date(LocalDate.now())
    .addItem(new OrderItem.Builder()
        .productId("P456")
        .quantity(2)
        .unitPrice(50.0)
        .build())
    .build();
```

### **2. Optional Fields with Defaults**
```java
User user = new User.UserBuilder()
    .name("Bob")
    .email("bob@example.com") // Optional
    .age(-1) // Default age if not set (requires validation)
    .build();
```

### **3. Validation Logic in Builder**
```java
public User build() {
    if (name == null || name.isEmpty()) throw new IllegalStateException("Name required");
    if (age < 0) throw new IllegalArgumentException("Age cannot be negative");
    return new User(this);
}
```

### **4. Builder with Builder (Nested Construction)**
```java
Address address = new Address.AddressBuilder()
    .street("123 Main St")
    .city("New York")
    .build();

User user = new User.UserBuilder()
    .name("Charlie")
    .address(address)
    .build();
```

---

## **Best Practices**

1. **Immutability:** Ensure the product is immutable (no setters).
2. **Validation:** Validate fields in the `build()` method.
3. **Default Values:** Provide sensible defaults for optional fields.
4. **Fluent API:** Return `this` or `Builder` from setter methods.
5. **Thread Safety:** If needed, make the builder thread-safe (e.g., using `AtomicReference`).
6. **Documentation:** Clearly document required vs. optional fields.
7. **Avoid Overuse:** Only use builders for complex objects; prefer constructors for simple ones.

---

## **Edge Cases & Pitfalls**
| **Scenario**               | **Solution**                                                                 |
|----------------------------|------------------------------------------------------------------------------|
| **Performance:** Builders add overhead for simple objects. | Use constructors for lightweight objects.                                  |
| **Serialization:** Builders may violate immutability. | Avoid serializing builders; serialize the product instead.                 |
| **Dependency Injection:** Builders can complicate DI. | Use constructor injection for dependencies; wire builders externally.     |
| **Testing:** Hard to mock builders. | Unit test components separately; prefer spies for integration tests.       |

---

## **Related Patterns**

| **Pattern**               | **Relationship**                                                                 | **When to Use Together**                                      |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------|
| **Factory Method**        | Alternative for simple object creation.                                         | Use builders for complex objects; factories for predefined variants. |
| **Prototype**             | Copies existing objects instead of constructing new ones.                       | Use builders to initialize prototypes.                         |
| **Factory Method + Builder** | Combine for hierarchical object creation (e.g., `DocumentFactory` + `SectionBuilder`). | When objects have both variations and nested complexity.      |
| **Immutable Object**      | Builders ensure immutability by design.                                          | Always pair builders with immutable products.                 |
| **Strategy**              | Builders can encapsulate construction strategies (e.g., "Lite" vs. "Full" build). | Use builders to switch between configurations.                 |
| **Decorator**             | Builders can dynamically add decorators (e.g., `ValidatorBuilder`).             | For runtime customization of object construction.            |

---

## **Language-Specific Variations**

### **1. Kotlin (DSL-Friendly)**
Kotlin’s `data class` + `copy()` combines immutability with builders:
```kotlin
data class User(val name: String, val age: Int, val email: String? = null)

fun userBuilder(block: UserBuilder.() -> Unit): User {
    return UserBuilder().apply(block).build()
}

class UserBuilder {
    var name: String = ""
    var age: Int = 0
    var email: String? = null

    fun build() = User(name, age, email)
}
```
**Usage:**
```kotlin
val user = userBuilder {
    name = "Diana"
    age = 25
}
```

### **2. Python (NamedTuple + dataclasses)**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: str
    age: int
    email: Optional[str] = None

def user_builder() -> UserBuilder:
    return UserBuilder()

class UserBuilder:
    def __init__(self):
        self.name: str = ""
        self.age: int = 0
        self.email: Optional[str] = None

    def name(self, name: str) -> "UserBuilder":
        self.name = name
        return self

    def age(self, age: int) -> "UserBuilder":
        self.age = age
        return self

    def email(self, email: Optional[str]) -> "UserBuilder":
        self.email = email
        return self

    def build(self) -> User:
        return User(self.name, self.age, self.email)
```

### **3. JavaScript (Object Spread + Closures)**
```javascript
const userBuilder = () => {
    let name, age, email;
    return {
        name: (n) => { name = n; return this; },
        age: (a) => { age = a; return this; },
        email: (e) => { email = e; return this; },
        build: () => ({ name, age, email })
    };
};
```
**Usage:**
```javascript
const user = userBuilder()
    .name("Eve")
    .age(33)
    .build();
```

---

## **When to Use the Builder Pattern**
| **Use Case**                          | **Pattern Fit**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|
| Objects with **10+ parameters**.      | Avoids "telescoping constructor" anti-pattern.                                  |
| **Optional parameters**.              | Provides clear defaults and validation.                                        |
| **Nested object construction**.       | Supports hierarchical or recursive builds (e.g., `ReportBuilder`).             |
| **Immutable objects**.               | Ensures thread-safe, unmodifiable products.                                     |
| **Fluent APIs** (e.g., configuration). | Enables readable method chaining (e.g., `spring.config().property("key").build()`). |
| **Testing**.                         | Isolates construction logic for mocking.                                        |

---

## **Alternatives**
- **Constructor Overloading:** Use for simple objects with a few variations.
- **Setter Methods:** Avoid if the object is mutable or complex.
- **JSON/XML Parsers:** For deserialization (e.g., Jackson, Gson).

---
**Final Note:** The Builder Pattern excels at **decoupling construction logic** while maintaining **readability and flexibility**. For most complex object scenarios, it is the preferred choice over raw constructors or setters.