# **[Design Pattern] Strategy Pattern Reference Guide**

---

## **Overview**
The **Strategy Pattern** is a behavioral design pattern that enables selecting an algorithm’s behavior at runtime. It defines a family of interchangeable algorithms, encapsulates each one as a separate class, and makes them interchangeable inside a context object. This pattern avoids conditional statements (e.g., `switch`/`if-else`) that dictate behavior, promoting open/closed principle and easier maintenance.

Key benefits:
- **Decouples** algorithm implementation from usage.
- **Encourages extensibility** by allowing new strategies to be added without modifying existing code.
- **Simplifies testing** via strategy isolation.
- **Optimizes flexibility** by switching behaviors dynamically.

Common use cases include payment methods, logging strategies, compression algorithms, and sorting criteria.

---

## **Schema Reference**

| **Component**       | **Description**                                                                                                                                                                                                 | **Relationships**                                                                 |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Strategy**         | Abstract/base interface defining a common method (e.g., `execute()`) for all concrete strategies.                                                                                                           | Implemented by **ConcreteStrategy** subclasses; used by **Context**.                |
| **ConcreteStrategy** | Implements the `Strategy` interface with specific algorithm logic. Example: `PayPalStrategy`, `CreditCardStrategy`.                                                                                     | Inherits from `Strategy`; injected into **Context**.                              |
| **Context**          | Maintains a reference to a `Strategy` object and delegates operations to it. Can switch strategies at runtime.                                                                                       | Holds Strategy object; delegates calls to `strategy.execute()` or similar.           |
| **Client**           | Interacts with **Context** to configure and invoke strategies. Typically unaware of concrete strategy classes.                                                                                       | Instantiates/sets **Context**; triggers strategy execution (e.g., `context.execute()`). |

---

## **Implementation Details**

### **1. Core Code Structure**
Below is a minimal implementation in **Java** (adaptable to other languages):

```java
// 1. Strategy Interface
public interface PaymentStrategy {
    void pay(double amount);
}

// 2. Concrete Strategies
public class CreditCardStrategy implements PaymentStrategy {
    private String cardNumber;
    public CreditCardStrategy(String cardNumber) { this.cardNumber = cardNumber; }
    @Override public void pay(double amount) { /* Logic */ }
}

public class PayPalStrategy implements PaymentStrategy {
    private String email;
    public PayPalStrategy(String email) { this.email = email; }
    @Override public void pay(double amount) { /* Logic */ }
}

// 3. Context
public class PaymentContext {
    private PaymentStrategy strategy;
    public void setStrategy(PaymentStrategy strategy) { this.strategy = strategy; }
    public void executePayment(double amount) {
        strategy.pay(amount); // Delegates to the selected strategy
    }
}

// 4. Client Usage
public class ShoppingCart {
    private PaymentContext context;
    public void checkout(double amount, PaymentStrategy strategy) {
        context.setStrategy(strategy);
        context.executePayment(amount);
    }
}
```

---

### **2. Best Practices**
1. **Favor Composition over Inheritance**:
   - Strategies are composed (not inherited) into the `Context`, allowing dynamic switching.

2. **Keep Strategies Stateless**:
   - Avoid mutable state in strategies to ensure thread safety and reusability. If state is needed, pass it via constructor.

3. **Document Strategy Contracts**:
   - Clearly define the `Strategy` interface’s methods and their preconditions/postconditions.

4. **Minimize Context Complexity**:
   - Limit the `Context` to delegating calls; avoid embedding strategy logic directly.

5. **Use Dependency Injection (DI)**:
   - Inject strategies into the `Context` via constructor, factory, or setter methods (as shown above).

6. **Avoid Overly Granular Strategies**:
   - Balance strategy granularity. Too many fine-grained strategies increase complexity.

7. **Leverage Flyweight where Applicable**:
   - Share immutable strategy instances across contexts to reduce memory usage.

8. **Testing Strategies**:
   - Test each strategy independently (e.g., mock `Context` to verify `ConcreteStrategy` behavior).

---

### **3. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                                                      | **Solution**                                                                                     |
|----------------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Tight Coupling in Context**    | `Context` directly implements strategy logic, violating the pattern.                                         | Delegate ALL operations to the `Strategy` object.                                                |
| **Overusing Null Checks**       | Checking for `null` strategies in `Context` can lead to runtime errors.                                      | Use a default strategy or factory to ensure non-null references.                                  |
| **Strategy Objects as Singletons** | Immutability is broken if strategies rely on singleton state.                                               | Pass required state via constructor/arguments.                                                    |
| **Strategies Modifying Shared State** | Concurrent modifications can lead to race conditions.                                                        | Ensure strategies are stateless or thread-safe.                                                   |
| **Cascading Strategy Changes**   | Changing one strategy breaks unrelated parts of the system.                                                   | Isolate strategies and ensure minimal dependencies.                                               |

---

## **Query Examples**

### **Example 1: Payment System**
**Scenario**: A shopping cart supports multiple payment methods at runtime.

```java
// Client code
ShoppingCart cart = new ShoppingCart();
cart.checkout(100, new CreditCardStrategy("4111-1111-1111-1111")); // Switches to CreditCard
cart.checkout(50, new PayPalStrategy("user@example.com"));           // Switches to PayPal
```

---

### **Example 2: Logging Strategies**
**Scenario**: A logger dynamically selects log formats (JSON, XML, plain text).

```java
public interface LogStrategy {
    void log(String message);
}

public class JsonLogStrategy implements LogStrategy { ... }
public class PlainTextLogStrategy implements LogStrategy { ... }

public class LoggerContext {
    private LogStrategy strategy;
    public void setStrategy(LogStrategy strategy) { this.strategy = strategy; }
    public void logMessage(String msg) { strategy.log(msg); }
}

// Client
LoggerContext logger = new LoggerContext();
logger.setStrategy(new JsonLogStrategy());
logger.logMessage("Critical error"); // Logs in JSON format
```

---

### **Example 3: Sorting Algorithms**
**Scenario**: A data processor uses different sorting algorithms (QuickSort, MergeSort).

```java
public interface SortStrategy {
    List<Integer> sort(List<Integer> data);
}

public class QuickSortStrategy implements SortStrategy { ... }
public class MergeSortStrategy implements SortStrategy { ... }

public class DataProcessor {
    private SortStrategy strategy;
    public void setStrategy(SortStrategy strategy) { this.strategy = strategy; }
    public List<Integer> process(List<Integer> data) {
        return strategy.sort(data);
    }
}

// Client
DataProcessor processor = new DataProcessor();
processor.setStrategy(new QuickSortStrategy());
List<Integer> sortedData = processor.process(rawData);
```

---

## **Performance Considerations**
| **Aspect**               | **Impact**                                                                                          | **Mitigation**                                                                                     |
|---------------------------|------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Strategy Switching Cost** | Changing strategies at runtime may involve object creation or memory reallocation.                   | Cache frequently used strategies or reuse immutable instances.                                     |
| **Overhead of Interface** | Abstract methods introduce minor overhead (e.g., virtual dispatch in Java).                          | Use lightweight interfaces or templates for performance-critical cases.                           |
| **Memory Usage**         | Each concrete strategy may consume memory.                                                            | Apply the **Flyweight Pattern** to share immutable strategy states.                                |
| **Cold Start Latency**   | Loading strategies dynamically (e.g., from plugins) can delay execution.                           | Preload strategies or use lazy initialization.                                                    |

---

## **Related Patterns**

| **Pattern**               | **Relationship**                                                                                                                                                     | **When to Use Together**                                                                           |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Factory Method**        | Strategies can be created via factories (e.g., `PaymentStrategyFactory`).                                                                                           | When strategy creation requires complex logic (e.g., validation, configuration).                    |
| **Template Method**       | The `Context` can follow a template method to standardize strategy execution (e.g., pre/post-processing).                                                      | When strategies share common setup/teardown steps.                                                |
| **Observer**              | Strategies can notify observers of changes (e.g., logging strategies alerting monitoring systems).                                                          | For event-driven strategy behaviors.                                                               |
| **Flyweight**             | Share immutable strategies across contexts to reduce memory.                                                                                                   | When multiple contexts use the same strategy instance.                                             |
| **Proxy**                 | Wrap strategies for lazy loading, access control, or logging.                                                                                                   | For strategies with expensive initialization or restricted access.                                 |
| **Command**               | Encapsulate strategy execution in commands for undo/redo or queuing.                                                                                            | When strategies need transactional support or history tracking.                                    |
| **State**                 | Strategies can model different states (e.g., "ActivePaymentStrategy" vs. "FailedPaymentStrategy").                                                       | When strategies represent distinct system states.                                                   |
| **Visitor**               | Strategies can be extended with new operations using Visitor without modifying existing strategy classes.                                                       | For adding new behaviors to existing strategies dynamically.                                       |

---

## **When to Apply the Strategy Pattern**
| **Use Case**                          | **Example**                                                                                                                                                     | **Alternatives**                                                                                     |
|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Varying Algorithm Selection**       | Different sorting algorithms for a dataset.                                                                                                                     | **If-else** (less flexible), **Decorator Pattern** (if algorithms are layered).                 |
| **Runtime Policy Configuration**      | Dynamic adjustment of payment methods in an e-commerce system.                                                                                                  | **Configuration files** (static), **Command Pattern** (if immutable).                              |
| **Plugin-Based Extensibility**        | Allowing third-party loggers to integrate into an application.                                                                                                    | **Adapter Pattern** (if interfaces are incompatible), **Dependency Injection**.                    |
| **Avoiding Conditional Logic**         | Replacing `switch-case` blocks with strategy delegation.                                                                                                       | **State Pattern** (if states are mutually exclusive), **Polymorphism** (simpler if few variants). |
| **Testing Complex Logic**              | Isolating strategies for unit testing (e.g., mocking a `PaymentStrategy`).                                                                                     | **Mocking frameworks** (e.g., Mockito), **Dependency Injection**.                                    |

---

## **Code Snippets by Language**

### **Python**
```python
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount):
        pass

class CreditCardStrategy(PaymentStrategy):
    def __init__(self, card_number):
        self.card_number = card_number
    def pay(self, amount):
        print(f"Paid ${amount} via Credit Card {self.card_number}")

class PayPalStrategy(PaymentStrategy):
    def __init__(self, email):
        self.email = email
    def pay(self, amount):
        print(f"Paid ${amount} via PayPal {self.email}")

class PaymentContext:
    def __init__(self, strategy: PaymentStrategy):
        self._strategy = strategy
    def set_strategy(self, strategy: PaymentStrategy):
        self._strategy = strategy
    def execute_payment(self, amount):
        self._strategy.pay(amount)

# Client
context = PaymentContext(CreditCardStrategy("4111-1111-1111-1111"))
context.execute_payment(100)
context.set_strategy(PayPalStrategy("user@example.com"))
context.execute_payment(50)
```

### **JavaScript/TypeScript**
```typescript
interface PaymentStrategy {
    pay(amount: number): void;
}

class CreditCardStrategy implements PaymentStrategy {
    constructor(private cardNumber: string) {}
    pay(amount: number): void {
        console.log(`Paid $${amount} via Credit Card ${this.cardNumber}`);
    }
}

class PayPalStrategy implements PaymentStrategy {
    constructor(private email: string) {}
    pay(amount: number): void {
        console.log(`Paid $${amount} via PayPal ${this.email}`);
    }
}

class PaymentContext {
    private strategy: PaymentStrategy;
    constructor(strategy: PaymentStrategy) { this.strategy = strategy; }
    setStrategy(strategy: PaymentStrategy): void { this.strategy = strategy; }
    executePayment(amount: number): void {
        this.strategy.pay(amount);
    }
}

// Client
const context = new PaymentContext(new CreditCardStrategy("4111-1111-1111-1111"));
context.executePayment(100);
context.setStrategy(new PayPalStrategy("user@example.com"));
context.executePayment(50);
```

### **C#**
```csharp
public interface IPaymentStrategy
{
    void Pay(double amount);
}

public class CreditCardStrategy : IPaymentStrategy
{
    private string _cardNumber;
    public CreditCardStrategy(string cardNumber) => _cardNumber = cardNumber;
    public void Pay(double amount) => Console.WriteLine($"Paid ${amount} via Credit Card {_cardNumber}");
}

public class PayPalStrategy : IPaymentStrategy
{
    private string _email;
    public PayPalStrategy(string email) => _email = email;
    public void Pay(double amount) => Console.WriteLine($"Paid ${amount} via PayPal {_email}");
}

public class PaymentContext
{
    private IPaymentStrategy _strategy;
    public void SetStrategy(IPaymentStrategy strategy) => _strategy = strategy;
    public void ExecutePayment(double amount) => _strategy.Pay(amount);
}

// Client
var context = new PaymentContext();
context.SetStrategy(new CreditCardStrategy("4111-1111-1111-1111"));
context.ExecutePayment(100);
context.SetStrategy(new PayPalStrategy("user@example.com"));
context.ExecutePayment(50);
```

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                                                                                     | **Solution**                                                                                       |
|-------------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Runtime Errors with Null Strategies** | `Context` does not validate strategy object before execution.                                    | Initialize with a default strategy or use `Optional` (Java) / `null` checks.                   |
| **Performance Degradation**         | Excessive strategy switching or complex strategy logic.                                            | Profile to identify bottlenecks; optimize or cache strategies.                                   |
| **Violating Open/Closed Principle** | Adding a new strategy requires modifying `Context`.                                                 | Ensure all strategies adhere to the abstract `Strategy` interface.                                |
| **Tight Coupling Between Strategies** | Strategies share dependencies (e.g., database access).                                           | Inject dependencies via constructors or interfaces.                                               |
| **Thread Safety Issues**            | Mutable strategies cause race conditions in multi-threaded environments.                          | Make strategies immutable or use synchronization.                                                |

---

## **Further Reading**
1. **Books**:
   - *Head First Design Patterns* (Kohl & VanHuss) – Intuitive explanations with examples.
   - *Design Patterns: Elements of Reusable Object-Oriented Software* (Gamma et al.) – Original Gang of Four reference.

2. **Online Resources**:
   - [Refactoring.Guru: Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
   - [Medium: When to Use Strategy Pattern](https://medium.com/@adityamurali/when-to-use-strategy-pattern-a48121f7883a)

3. **Tools**:
   - **Static Analysis**: Tools like SonarQube can detect violations of strategy pattern misuse (e.g., `switch-case` instead of delegation).
   - **Mocking Frameworks**: MockK (Kotlin), Mockito (Java), or Jasmine (JavaScript) for testing strategies.