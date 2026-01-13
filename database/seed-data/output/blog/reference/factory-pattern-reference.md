# **[Design Pattern] Factory Pattern Reference Guide**

---

## **Overview**
The **Factory Pattern** is a **creational design pattern** that defines an interface for creating objects in a superclass but allows subclasses to decide which class to instantiate. It **decouples object creation from usage**, promoting flexibility, maintainability, and adherence to the **Open/Closed Principle** (open for extension, closed for modification). The pattern comes in three variants:
- **Simple Factory** (non-pattern, but often confused)
- **Factory Method** (delegates instantiation to subclasses)
- **Abstract Factory** (creates families of related objects).

Use the Factory Pattern when:
✔ You don’t know ahead of time the exact types and dependencies of objects your code should work with.
✔ You want to **avoid tight coupling** between client code and concrete classes.
✔ You need to **satisfy the Dependency Inversion Principle** (depend on abstractions).
✔ You must **support subclasses** with different configurations (e.g., UI themes, payment methods).

**Key Benefit:** Clients interact only with abstract interfaces, reducing dependency on concrete implementations.

---

## **Schema Reference**

| **Component**          | **Purpose**                                                                                     | **Example Code (Java)**                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Creator**            | Declares the factory interface for creating products.                                            | `interface FoodFactory { Food createFood(); }`                                         |
| **Concrete Creator**   | Implements the Creator’s method and returns a concrete product.                                | `class PizzaFactory implements FoodFactory { public Pizza createFood() { ... } }`      |
| **Product**            | Interface or abstract class defining the common interface for objects the factory creates.      | `interface Food { void prepare(); }`                                                   |
| **Concrete Product**   | Implements the Product interface.                                                              | `class Pizza implements Food { public void prepare() { ... } }`                        |
| **Client**             | Uses the Creator to create objects without knowing the concrete class.                          | `FoodFactory factory = new PizzaFactory(); factory.createFood().prepare();`             |

---

## **Implementation Details by Variant**

### **1. Simple Factory (Anti-Pattern, but Common Misuse)**
*A static method that acts as a centralized switch to instantiate objects.*

#### **When to Use?**
- For **one-off factory methods** (not extensible for subclasses).
- When **design constraints** prohibit creating subclasses.

#### **Example (Java)**
```java
public class SimpleFoodFactory {
    public static Food createFood(String type) {
        switch (type) {
            case "PIZZA": return new Pizza();
            case "BURGER": return new Burger();
            default: throw new IllegalArgumentException("Invalid food type.");
        }
    }
}
```
**Pros:**
✔ Simple, low overhead.
**Cons:**
❌ Violates **Open/Closed Principle** (hard to add new types without modifying).
❌ Tight coupling to concrete implementations.

---

### **2. Factory Method Pattern**
*Defines an **interface** for creating objects but lets subclasses decide which class to instantiate.*

#### **When to Use?**
- When a class can’t anticipate the type of objects it must create.
- When you want **subclasses to specify the objects the creator makes**.

#### **Example (Java)**
```java
// Creator (abstract)
abstract class FoodCreator {
    public Food orderFood() {
        Food food = createFood();
        food.prepare();
        return food;
    }
    abstract Food createFood(); // Factory method
}

// Concrete Creator
class PizzaCreator extends FoodCreator {
    @Override
    Food createFood() { return new Pizza(); }
}

// Client
FoodCreator creator = new PizzaCreator();
Food food = creator.orderFood();
```
**Pros:**
✔ Extensible via subclasses.
✔ Decouples client from object creation.
**Cons:**
❌ Requires subclassing (less flexible than Abstract Factory).

---

### **3. Abstract Factory Pattern**
*Provides an interface for creating **families of related objects** without specifying concrete classes.*

#### **When to Use?**
- When a system needs to be **independent of how objects are created**.
- When you need **product families** (e.g., UI themes: Windows/Linux/Mac buttons, scrollbars).

#### **Example (Java)**
```java
// Abstract Product A
interface Button { void render(); }

// Concrete Product A
class WindowsButton implements Button {
    public void render() { System.out.println("Rendering Windows button"); }
}

// Abstract Factory
interface GUIFactory {
    Button createButton();
}

// Concrete Factory
class WindowsFactory implements GUIFactory {
    public Button createButton() { return new WindowsButton(); }
}

// Client
GUIFactory factory = new WindowsFactory();
Button button = factory.createButton();
button.render();
```
**Pros:**
✔ Supports **families of related objects**.
✔ Easy to add new product families.
**Cons:**
❌ Complex for small-scale object creation.

---

## **Best Practices & Pitfalls**

### **✅ Best Practices**
1. **Use Interfaces, Not Concrete Classes**
   - Always inject dependencies via interfaces (e.g., `FoodFactory`, not `PizzaFactory`).
2. **Favor the Factory Method Over Simple Factory**
   - Simple factories are often overused; prefer hierarchy-based solutions.
3. **Cache Factories When Possible**
   - Reuse factory instances (e.g., singleton) to avoid overhead.
4. **Document Assumptions**
   - Clearly specify which classes the factory can instantiate.
5. **Leverage Dependency Injection (DI)**
   - Use frameworks like Spring or Guice to manage factories.

### **❌ Common Pitfalls**
1. **Tight Coupling in Clients**
   - Avoid hardcoding factory types (e.g., `new PizzaFactory()`). Use DI instead.
2. **Overusing Abstract Factories**
   - For simple cases, a **Factory Method** suffices.
3. **Violating the Single Responsibility Principle**
   - A factory should **only** create objects; don’t mix logic.
4. **Hidden Complexity**
   - Ensure factories are easy to test and mock.

---

## **Query Examples**

### **1. Creating a Product via Factory Method**
**Scenario:** Order a pizza via a factory method.
```java
FoodCreator creator = new PizzaCreator();
Food pizza = creator.orderFood(); // Creations delegated to PizzaCreator.createFood()
```

### **2. Abstract Factory for UI Components**
**Scenario:** Load a Windows theme.
```java
GUIFactory factory = new WindowsFactory();
Button button = factory.createButton(); // Gets WindowsButton
ScrollBar scrollbar = factory.createScrollBar(); // Gets WindowsScrollBar
```

### **3. Dynamic Factory Selection**
**Scenario:** Change factory at runtime (e.g., based on config).
```java
String theme = Config.getTheme();
GUIFactory factory;
if (theme.equals("Windows")) {
    factory = new WindowsFactory();
} else if (theme.equals("Mac")) {
    factory = new MacFactory();
}
Button button = factory.createButton();
```

### **4. Unit Testing Factories**
**Test Strategy:** Mock factories to isolate creation logic.
```java
// Mock Factory for PizzaCreator
FoodFactory mockFactory = mock(FoodFactory.class);
when(mockFactory.createFood()).thenReturn(new Pizza());
FoodCreator creator = new PizzaCreator(mockFactory); // Inject dependency
Food food = creator.orderFood(); // Verifies mock behavior
```

---

## **Related Patterns**

| **Pattern**            | **Relationship**                                                                 | **Use Case**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Builder**            | Often used with Factory Pattern to create complex objects step-by-step.       | Configuring objects with many optional parameters (e.g., `PizzaBuilder`).    |
| **Singleton**          | Factories can enforce singleton patterns for global instances.                  | Managing a single database connection factory.                              |
| **Dependency Injection (DI)** | Factories integrate with DI containers (e.g., Spring) for loose coupling.   | Injecting factories into services via `@Autowired` or constructor injection. |
| **Prototype**          | Alternative to Factory when cloning existing objects is cheaper than creating new ones. | Caching prototypes for performance-critical objects.                        |
| **Strategy**           | Factories can instantiate different algorithms (strategies).                   | Switching sorting algorithms at runtime via a `SortingFactory`.              |

---

## **Further Reading**
- **GoF Book:** *Design Patterns: Elements of Reusable Object-Oriented Software* (Factory Method, Abstract Factory).
- **Martin Fowler:** ["Factory Method Pattern"](https://martinfowler.com/eaaCatalog/factoryMethod.html).
- **Java Doc:** [`java.util.Calendar#getInstance()`](https://docs.oracle.com/javase/8/docs/api/java/util/Calendar.html#getInstance--) (Simple Factory example).
- **Clean Code:** *Robert Martin* (Avoid "factory methods" in favor of dependency injection).