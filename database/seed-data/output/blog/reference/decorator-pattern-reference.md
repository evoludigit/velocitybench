# **Decorator Pattern Reference Guide**
*Adding Behavior Dynamically to Objects*

---

## **Overview**
The **Decorator Pattern** is a structural design pattern that allows behavior to be added to individual objects *dynamically* without affecting the behavior of other objects from the same class. Rather than using inheritance to extend functionality (which creates a "class explosion"), the Decorator Pattern wraps an object with additional behavior in a flexible, modular way. This pattern is particularly useful when you need to add responsibilities to objects at runtime, support multiple variations of an object, or avoid permanent subclassing.

The Decorator follows the **Open/Closed Principle** ("open for extension, closed for modification") by allowing new behaviors to be added without modifying existing code. It is widely used in GUI frameworks, logging systems, and IoC (Inversion of Control) containers.

---

## **Key Concepts**
| Term               | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Component**      | The interface for objects that can have responsibilities added to them dynamically.             |
| **Concrete Component** | Objects that define default behavior for the Component interface.                              |
| **Decorator**      | Maintains a reference to a Component object and defines an interface identical to the Component.|
| **Concrete Decorator** | Adds new behavior to the Component object by overriding methods in the Decorator.            |

---

## **Schema Reference**
The Decorator Pattern consists of the following class structures:

| Class/Interface       | Purpose                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------|
| **Component**         | Declares the interface for objects that can be decorated.                                   |
|                       | Example: `interface Shape { void draw(); }`                                               |
| **ConcreteComponent** | Defines default behavior for the interface.                                                |
|                       | Example: `class Circle implements Shape { void draw() { drawCircle(); } }`                 |
| **Decorator**         | Maintains a reference to a Component and delegates all operations to it.                      |
|                       | Example: `abstract class ShapeDecorator implements Shape { protected Shape shape; }`       |
| **ConcreteDecorator** | Adds new behavior before/after delegating to the wrapped Component.                          |
|                       | Example: `class RedShapeDecorator extends ShapeDecorator { void draw() { System.out.println("Red"); shape.draw(); } }` |

---

## **Implementation Patterns**
### **1. Class-Based Decorators (OOP Style)**
- **Pros**: Simple, intuitive, and works well in pure OOP languages (Java, C++).
- **Cons**: Can lead to a deep inheritance hierarchy.
- **Example**:
  ```java
  interface Shape {
      void draw();
  }

  class Circle implements Shape {
      void draw() { System.out.println("Drawing Circle"); }
  }

  class ShapeDecorator implements Shape {
      protected Shape wrapped; // Reference to the Component
      ShapeDecorator(Shape shape) { this.wrapped = shape; }

      @Override
      public void draw() { wrapped.draw(); }
  }

  class RedShapeDecorator extends ShapeDecorator {
      RedShapeDecorator(Shape shape) { super(shape); }

      @Override
      public void draw() {
          System.out.println("Border in Red");
          super.draw();
      }
  }

  // Usage:
  Shape circle = new Circle();
  Shape redCircle = new RedShapeDecorator(circle);
  redCircle.draw(); // Output: "Border in Red" + "Drawing Circle"
  ```

---

### **2. Object-Based Decorators (Dependency Injection)**
- **Pros**: More flexible (works with any language, including functional ones). Avoids deep inheritance.
- **Cons**: Requires composition over inheritance.
- **Example (Python)**:
  ```python
  from abc import ABC, abstractmethod

  class Shape(ABC):
      @abstractmethod
      def draw(self):
          pass

  class Circle(Shape):
      def draw(self):
          print("Drawing Circle")

  class ShapeDecorator(Shape):
      def __init__(self, component):
          self._component = component

      def draw(self):
          self._component.draw()

  class RedShapeDecorator(ShapeDecorator):
      def draw(self):
          print("Border in Red")
          super().draw()

  # Usage:
  circle = Circle()
  red_circle = RedShapeDecorator(circle)
  red_circle.draw()  # Output: "Border in Red" + "Drawing Circle"
  ```

---

### **3. Decorator with Interface (Cleaner Abstraction)**
- **Best Practice**: Define a base decorator interface to ensure consistency.
- **Example (C#)**:
  ```csharp
  public interface IShape
  {
      void Draw();
  }

  public class Circle : IShape
  {
      public void Draw() => Console.WriteLine("Drawing Circle");
  }

  public abstract class ShapeDecorator : IShape
  {
      protected IShape _shape;
      protected ShapeDecorator(IShape shape) { _shape = shape; }

      public virtual void Draw() => _shape.Draw();
  }

  public class RedBorderDecorator : ShapeDecorator
  {
      public RedBorderDecorator(IShape shape) : base(shape) { }
      public override void Draw()
      {
          Console.WriteLine("Red Border");
          base.Draw();
      }
  }

  // Usage:
  var circle = new Circle();
  var redCircle = new RedBorderDecorator(circle);
  redCircle.Draw(); // Output: "Red Border" + "Drawing Circle"
  ```

---

## **Best Practices**
1. **Prefer Composition Over Inheritance**
   - Use Decorators to avoid bloated class hierarchies.
2. **Keep Decorators Simple**
   - Each decorator should have a single responsibility.
3. **Use Dependency Injection**
   - Pass dependencies (e.g., loggers, validators) via constructors for better testability.
4. **Avoid Overusing Decorators**
   - If behavior requires configuration, consider the **Strategy Pattern** instead.
5. **Document Behavior Clearly**
   - Use method names like `withLogging()`, `withValidation()` for clarity.

---

## **Query Examples**
### **1. Adding Logging Decorator (Java)**
```java
class LoggingDecorator extends ShapeDecorator {
    LoggingDecorator(Shape shape) { super(shape); }

    @Override
    public void draw() {
        System.out.println("Logging: Enter draw()");
        super.draw();
        System.out.println("Logging: Exit draw()");
    }
}

// Usage:
Shape circle = new Circle();
Shape loggedCircle = new LoggingDecorator(circle);
loggedCircle.draw();
// Output:
// Logging: Enter draw()
// Drawing Circle
// Logging: Exit draw()
```

---

### **2. Chaining Multiple Decorators (Python)**
```python
class ValidationDecorator(ShapeDecorator):
    def draw(self):
        if self._component is None:
            raise ValueError("Component cannot be None")
        super().draw()

class LoggingDecorator(ShapeDecorator):
    def draw(self):
        print("Start drawing")
        super().draw()
        print("Finished drawing")

# Usage:
circle = Circle()
validated = ValidationDecorator(circle)
logged = LoggingDecorator(validated)

logged.draw()
# Output:
# Start drawing
# Drawing Circle
# Finished drawing
```

---

### **3. Dynamic Decoration (Spring Boot)**
```java
@Component
public class ShapeDecorator {
    private final Shape shape;

    @Autowired
    public ShapeDecorator(Shape shape) {
        this.shape = shape;
    }

    public void draw() {
        System.out.println("Decorator behavior");
        shape.draw();
    }
}

// Auto-wiring in a Spring context:
@SpringBootApplication
public class App {
    @Autowired
    private ShapeDecorator decorator;

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
        decorator.draw(); // Output: "Decorator behavior" + "Drawing Circle"
    }
}
```

---

## **Common Pitfalls & Solutions**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| **Decorator Stack Overhead**     | Limit the number of decorators; use composition patterns instead.       |
| **Complexity in Debugging**      | Add clear logging or use named decorators (e.g., `LoggingDecorator`).    |
| **Infinite Recursion**           | Ensure decorators properly delegate to the wrapped object.               |
| **Violating Single Responsibility** | Split decorators into smaller, focused classes.                       |

---

## **When to Use the Decorator Pattern**
✅ **Add responsibilities to objects dynamically** (e.g., logging, validation).
✅ **Support multiple variations of an object at runtime** (e.g., GUI widgets with different behaviors).
✅ **Avoid subclassing explosion** (when inheritance would create too many classes).

❌ **Avoid when:**
- Behavior is static (use **Strategy Pattern** instead).
- Performance is critical (decorators add slight overhead).
- The decorator logic is too complex (consider **Composite Pattern**).

---

## **Related Patterns**
| Pattern                  | Relationship to Decorator Pattern                          |
|--------------------------|----------------------------------------------------------|
| **Strategy Pattern**     | Both add behavior dynamically, but Decorator wraps an object, while Strategy replaces it. |
| **Proxy Pattern**        | Similar structure (wraps an object), but Proxy controls access rather than adding behavior. |
| **Composite Pattern**    | Both use composition, but Composite builds tree structures, while Decorator adds layers. |
| **Adapter Pattern**      | Adapters convert interfaces; Decorators add responsibilities. |
| **Chain of Responsibility** | Both involve delegation, but Chain handles request processing linearly. |

---

## **Conclusion**
The **Decorator Pattern** is a powerful tool for extending object behavior dynamically without inheritance. By wrapping objects with decorators, you can create flexible, modular, and maintainable designs.

**Key Takeaways:**
- Use decorators to add behavior *at runtime*.
- Prefer composition over inheritance.
- Keep decorators focused on a single responsibility.
- Leverage dependency injection for better testability.

For further reading, explore how Decorators are used in frameworks like **Spring AOP** or **Java Streams** (where `map`, `filter` act as decorators).