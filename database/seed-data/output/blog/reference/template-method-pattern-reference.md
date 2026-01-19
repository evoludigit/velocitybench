# **[Design Pattern] Template Method Pattern – Reference Guide**

---

## **Overview**
The **Template Method Pattern** is a **behavioral design pattern** that defines the *skeleton* of an algorithm in a base class, while allowing subclasses to override specific steps without changing the overall structure. It promotes **code reuse** by encapsulating invariant logic in parent classes and delegating variable parts to child implementations.

This pattern is useful when:
- You need to control the **execution flow** of a complex algorithm while allowing customization of certain steps.
- A subclass should redefine only selected parts of an algorithm, leaving the rest intact.
- You want to **prevent duplication** of boilerplate code across subclasses.

Unlike **Strategy** (which replaces entire algorithms), Template Method keeps the algorithm’s structure fixed while enabling flexibility in key operations.

---

## **Schema Reference**
Below are the key components and their relationships in the Template Method Pattern.

| **Component**       | **Description**                                                                                     | **Example Fields/Methods**                     |
|----------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Abstract Class**   | Defines the *template method* (algorithm skeleton) and declares abstract operations to be overridden. | `finalize()`, `getData()`                     |
| **Concrete Class**   | Implements the abstract methods to provide concrete behavior for the algorithm’s variable steps.   | `ConcreteClassA`, `ConcreteClassB`          |
| **Template Method**  | Controls the **order of operations** in the algorithm (typically marked `final`).                   | `execute()`                                    |
| **Hook Methods**     | Optional steps that subclasses *may* override (e.g., for extensibility without breaking the skeleton). | `hookBeforeStep()`, `hookAfterStep()`          |

---

## **Implementation Details**
### **Key Concepts**
1. **Template Method**
   - A method in the base class that defines the **top-level algorithmic structure**.
   - Calls abstract or concrete methods to execute steps.
   - Often declared `final` to prevent subclass redefinition of the skeleton.

   ```java
   public abstract class DataProcessor {
       public final void execute() {  // Template Method
           preProcess();
           processData();           // Abstract method (subclass defines)
           postProcess();
       }

       protected void preProcess() {}  // Default hook
       protected abstract void processData();  // Must be implemented
   }
   ```

2. **Abstract Methods**
   - Placeholders for steps that *must* be implemented by subclasses.
   - Enforce the algorithm’s requirements.

3. **Hook Methods**
   - Optional methods that subclasses *can* override (e.g., for conditional logic).
   - Allow flexibility without breaking the template.

   ```java
   public void execute() {
       preProcess();
       if (isAdvancedMode()) {  // Hook
           advancedLogic();
       }
       processData();
   }
   ```

4. **Final Methods**
   - Used to prevent subclasses from altering the algorithm’s flow (e.g., `execute()`).

---

### **Best Practices**
- **Minimize Abstract Methods**: Only declare steps that *must* vary.
- **Use `protected` Access**: Allow subclasses to call internal steps indirectly.
- **Avoid Deep Inheritance**: Template Method can lead to the **"Fragile Base Class"** problem. Prefer composition or **Strategy** for complex variations.
- **Document Overridable Methods**: Clarify which steps are customizable (e.g., via `@Override` or comments).

---
### **Example: Document Processing**
```java
// Abstract template class
public abstract class DocumentRenderer {
    public final void render() {  // Template Method
        collectData();
        formatHeader();
        renderContent();  // Abstract method
        formatFooter();
    }

    protected abstract void renderContent();  // Must be implemented

    private void formatHeader() {  // Concrete method
        System.out.println("=== Document Start ===");
    }

    private void collectData() {  // Hook (customizable)
        System.out.println("Fetching data...");
    }
}

// Concrete implementation
public class InvoiceRenderer extends DocumentRenderer {
    @Override
    protected void renderContent() {
        System.out.println("Rendering invoice items...");
    }
}
```

**Output**:
```
Fetching data...
=== Document Start ===
Rendering invoice items...
=== Document End ===
```

---

## **Query Examples**
### **1. When to Use Template Method vs. Other Patterns**
| **Pattern**          | **Template Method**                          | **Strategy**                          | **Observer**                 |
|-----------------------|-----------------------------------------------|----------------------------------------|-------------------------------|
| **Purpose**           | Define algorithm skeleton with customizable steps. | Replace entire algorithms dynamically. | Notify objects of state changes. |
| **Flexibility**       | Subclasses override *specific* steps.        | Swap algorithms at runtime.            | Decouples event sources/listeners. |
| **Use Case**          | Cookbook recipes (fixed steps, variable ingredients). | Sorting algorithms (swap implementations). | GUI event handling. |

**Example**: Use **Template Method** for a **game loop** where physics, rendering, and input handling are fixed, but *how* they’re implemented varies per game type.

---

### **2. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                      |
|---------------------------------------|------------------------------------------------------|
| **Tight Coupling**: Subclasses rely on internal state. | Use `protected` methods and avoid exposing implementation details. |
| **Violating Liskov Substitution**: Subclasses break the template’s logic. | Enforce contracts via abstract methods; validate inputs. |
| **Over-Use**: Overloading with hooks reduces maintainability. | Limit hooks to truly optional steps.                 |

---

### **3. Real-World Analogies**
- **Cooking**:
  - Template: A recipe’s steps (boil water → add pasta → drain).
  - Variable: Type of pasta (spaghetti vs. penne).
- **HTML Rendering**:
  - Template: `render()` calls `openTag()`, `addContent()`, `closeTag()`.
  - Variable: `addContent()` handles `<h1>`, `<p>`, etc.

---

## **Related Patterns**
| **Pattern**          | **Relation to Template Method**                                                                 |
|----------------------|------------------------------------------------------------------------------------------------|
| **Strategy**         | Both enable customization, but Template Method fixes the algorithm’s *flow* while Strategy allows *complete* algorithm swaps. |
| **Factory Method**   | Similar in delegation logic, but Factory Method creates objects, while Template Method defines behavior. |
| **Observer**         | Used alongside Template Method to notify steps (e.g., hooks) of changes.                         |
| **State**            | Can refactor variable steps into **State** objects for runtime behavior changes.               |
| **Decorator**        | Use Decorator to *extend* steps (e.g., wrap `renderContent()` with logging).                   |

---
## **When to Avoid**
- **When steps vary too widely**: Prefer **Strategy** or **Composer** patterns.
- **For simple, non-reusable logic**: Plain class methods may suffice.
- **In tightly coupled architectures**: Template Method can create rigid hierarchies.

---
## **Summary Checklist**
1. [ ] **Identify invariant steps** (skeleton) and variable ones (hooks/methods to override).
2. [ ] **Declare abstract methods** for required customization.
3. [ ] **Mark the template method as `final`** to prevent redefinition.
4. [ ] **Test subclass implementations** for correctness and performance.
5. [ ] **Document which steps are overrideable** (e.g., via Javadoc `@Override`).

---
**Example Code Repository**: [GitHub - TemplateMethodPattern](https://github.com/design-patterns-examples/template-method)
**Further Reading**:
- *Design Patterns: Elements of Reusable Object-Oriented Software* (GoF, Ch. 10).
- *Head First Design Patterns* (Kerievsky) – Visual analogy to cooking.