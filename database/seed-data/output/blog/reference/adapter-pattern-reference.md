---
# **[Design Pattern] Adapter Pattern Reference Guide**
*Making Incompatible Interfaces Compatible*

---

## **1. Overview**
The **Adapter Pattern** acts as a bridge between incompatible interfaces, enabling seamless communication between two systems that wouldn’t otherwise work together. Unlike other patterns that modify class structures, the Adapter Pattern **wraps an existing class** with a new interface, allowing it to conform to expectations of another system. This is particularly useful in:

- **Legacy system integration** (e.g., adding JPG support to a legacy BMP-only renderer).
- **Third-party library adoption** (e.g., using a payment processor with a different method signature).
- **API abstraction** (e.g., allowing new clients to use legacy code without modification).

There are two primary variants:
- **Class Adapter**: Uses **multiple inheritance** (subclassing) to adapt interfaces.
- **Object Adapter**: Uses **composition** (delegation) to adapt interfaces (more flexible, common in languages with single inheritance).

---

## **2. Schema Reference**

| **Component**       | **Responsibility**                                                                                     | **Example Class**               |
|---------------------|------------------------------------------------------------------------------------------------------|----------------------------------|
| **Target Interface**| Defines the domain-specific interface that clients expect.                                             | `PaymentProcessor`              |
| **Adaptee**         | The existing class with an incompatible interface to adapt.                                          | `LegacyPaymentGateway`          |
| **Adapter**         | Implements the `Target` interface while delegating to the `Adaptee`.                                | `PaymentGatewayAdapter`         |
| **Client**          | Uses the `Target` interface without knowing the `Adaptee` exists.                                     | `CheckoutService`               |

*(Visual Schema: See UML Diagram for relationships.)*

---

## **3. Key Implementation Details**

### **When to Use**
✅ **Pros:**
- **Reusable**: Adapters can be applied to multiple adaptees.
- **Non-invasive**: No changes needed to existing code.
- **Flexible**: Supports both class and object adapters.

❌ **Avoid When:**
- The adaptee is **read-only** (e.g., a `final` class in Java).
- The interface mismatch is **temporary** (refactor instead).
- The adapter becomes a **bottleneck** (consider a facade).

### **Structure**
Follow this implementation template (using **Object Adapter** in Java-style pseudocode):

```java
// Target Interface (Client's expectation)
interface PaymentProcessor {
    void processPayment(String amount);
}

// Adaptee (Incompatible legacy class)
class LegacyPaymentGateway {
    void legacyMethod(String amount, String currency) { ... }
}

// Adapter (Wraps Adaptee)
class PaymentGatewayAdapter implements PaymentProcessor {
    private LegacyPaymentGateway gateway;

    public PaymentGatewayAdapter(LegacyPaymentGateway legacy) {
        this.gateway = legacy;
    }

    @Override
    public void processPayment(String amount) {
        gateway.legacyMethod(amount, "USD"); // Map to legacy params
    }
}

// Client (Uses the Adapter transparently)
class CheckoutService {
    private PaymentProcessor processor;

    CheckoutService(PaymentProcessor processor) {
        this.processer = processor;
    }

    void checkout() {
        processor.processPayment("100.00"); // Works with any PaymentProcessor
    }
}
```

### **Best Practices**
1. **Fail Fast**: Validate adapter inputs to avoid unexpected behavior.
2. **Document Assumptions**: Note edge cases (e.g., "Adapter rejects null amounts").
3. **Avoid Over-Adapting**: Keep adapters simple; refactor core systems if possible.
4. **Thread Safety**: If the adaptee is stateful, ensure synchronization.
5. **Testing**: Test adapter boundaries (e.g., mock legacy calls).

---

## **4. Query Examples**
### **Example 1: Legacy Image Renderer (Object Adapter)**
**Problem**: A legacy app renders only `Bitmap` objects, but new code uses `JPEG`.
**Solution**:
```java
// Target
interface ImageRenderer {
    void render(Image image);
}

// Adaptee
class BitmapRenderer {
    void renderBitmap(Bitmap bitmap) { ... }
}

// Adapter
class JPEGToBitmapAdapter implements ImageRenderer {
    private BitmapRenderer renderer;

    JPEGToBitmapAdapter(BitmapRenderer renderer) {
        this.renderer = renderer;
    }

    @Override
    public void render(Image image) {
        Bitmap bitmap = image.toBitmap(); // Convert JPEG → Bitmap
        renderer.renderBitmap(bitmap);
    }
}
```

### **Example 2: Class Adapter (Subclassing)**
**Problem**: A legacy `USBPort` must work with a `TypeCConnector`.
**Solution** (Java doesn’t support multiple inheritance, but C++/Python does):
```cpp
// Adaptee
class USBPort {
public:
    void connectUSB() { ... }
};

// Target
class TypeCConnector {
public:
    virtual void connectTypeC() = 0;
};

// Adapter (Subclass both)
class USBToTypeCAdapter : public USBPort, public TypeCConnector {
    void connectTypeC() override {
        connectUSB(); // Delegate
    }
};
```

---

## **5. Common Pitfalls & Solutions**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| **Performance overhead**             | Cache adapter results if operations are expensive.                          |
| **Tight coupling to Adaptee**       | Use composition (Object Adapter) for flexibility.                            |
| **Maintenance burden**              | Document adapter logic clearly; consider refactoring legacy code.           |
| **Violating DRY principles**        | Share adapter logic via a factory pattern if multiple adapters reuse code.    |

---
## **6. Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Combine**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Facade**                | Both hide complexity, but Adapter changes interfaces; Facade simplifies calls.    | Use Adapter to integrate legacy systems behind a facade.                           |
| **Decorator**             | Adds behavior dynamically; Adapter adapts interfaces.                          | Chain an Adapter with a Decorator to extend adapted functionality.                  |
| **Bridge**                | Separates abstraction from implementation; Adapter reuses existing interfaces. | Use Bridge for incremental extensions; Adapter for quick compatibility.             |
| **Strategy**              | Defines interchangeable algorithms; Adapter adapts incompatible interfaces.    | Use Strategy for algorithm swapping; Adapter to plug in new strategies.              |

---
## **7. Key Takeaways**
✔ **Purpose**: Translate between incompatible interfaces without modifying original code.
✔ **Variants**: Object Adapter (composition) is more flexible than Class Adapter (inheritance).
✔ **Trade-offs**: Simple to implement but may obscure code complexity if overused.
✔ **Alternatives**: Consider **Facade** for simpler exposure or **Bridge** for extensibility.

---
**Further Reading**:
- *Design Patterns: Elements of Reusable Object-Oriented Software* (GoF).
- [Adapter Pattern on Refactoring.Guru](https://refactoring.guru/design-patterns/adapter).
- *"When to use Adapter vs. Decorator"* (Stack Overflow discussion).