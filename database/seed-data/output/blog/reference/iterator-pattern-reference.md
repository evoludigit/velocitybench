---
# **[Design Pattern] Iterator Pattern: Reference Guide**

---

## **Overview**
The **Iterator Pattern** provides a uniform way to traverse collections of objects without exposing their underlying representation. This pattern decouples iteration logic from the collection itself, enabling consistent traversal for heterogeneous containers (e.g., arrays, linked lists, trees). Key benefits include:
- **Code reusability**: Separates iteration code from collection logic.
- **Flexibility**: Supports multiple traversal directions (forward/backward) and custom iteration strategies.
- **Encapsulation**: Hides complexity of internal data structures.
- **Compatibility**: Standardizes iteration interfaces across different collections.

Ideal for collections where traversal order or access patterns vary (e.g., priority queues, bidirectional linked lists).

---

## **Schema Reference**

| **Element**               | **Description**                                                                                     | **Example Methods/Attributes**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| **Iterator**              | Interface defining iteration operations (e.g., `next()`, `hasNext()`).                              | `hasNext()`, `next()`, `remove()`                       |
| **ConcreteIterator**      | Implements `Iterator` for a specific collection type, tracking current position.                  | Internal iterator state (e.g., `currentIndex`)           |
| **Aggregate**             | Defines operations to create iterators (`createIterator()`).                                       | `createIterator()`, `getSize()`                         |
| **ConcreteAggregate**     | Implements `Aggregate` and provides iterators for its collection (e.g., arrays, trees).           | Concrete logic for iterator creation (e.g., `new ArrayIterator()`) |
| **Client Code**           | Uses iterators to traverse collections without knowing their internal structure.                   | `Iterator it = aggregate.createIterator();`             |

---

## **Implementation Details**

### **1. Core Components**
#### **Iterator Interface**
```java
public interface Iterator<T> {
    boolean hasNext();      // Checks if elements remain.
    T next();               // Returns next element; throws NoSuchElementException if none.
    void remove();          // Optional: Removes last returned element (if supported).
}
```

#### **Aggregate Interface**
```java
public interface Aggregate<T> {
    Iterator<T> createIterator();  // Returns a new iterator for traversal.
}
```

#### **Concrete Iterator**
- Maintains traversal state (e.g., `currentIndex`, `currentNode`).
- Implements `Iterator` methods by interacting with the collection’s internal structure.

#### **Concrete Aggregate**
- Implements `createIterator()` to return a `ConcreteIterator` tied to its data.
- Example for a `List`:
  ```java
  public class ConcreteList implements Aggregate<String> {
      private String[] items;

      @Override
      public Iterator<String> createIterator() {
          return new ConcreteListIterator(this);
      }

      private class ConcreteListIterator implements Iterator<String> {
          private int currentIndex;

          @Override
          public boolean hasNext() { return currentIndex < items.length; }
          @Override
          public String next() { return items[currentIndex++]; }
      }
  }
  ```

---

### **2. Use Cases**
#### **Forward-Only Iteration**
```java
Iterator<String> it = list.createIterator();
while (it.hasNext()) {
    System.out.println(it.next());
}
```

#### **Bidirectional Iteration**
Extend `Iterator` to add `hasPrevious()`/`previous()`:
```java
public interface BidirectionalIterator<T> extends Iterator<T> {
    boolean hasPrevious();
    T previous();
}
```

#### **Custom Iteration Strategies**
- **Reverse Iteration**: Modify `ConcreteIterator` to decrement indices.
- **Filtering Iteration**: Create a wrapper iterator that skips elements matching a condition:
  ```java
  public class FilterIterator<T> implements Iterator<T> {
      private Iterator<T> wrappedIterator;
      private Predicate<T> filter;

      public FilterIterator(Iterator<T> it, Predicate<T> filter) {
          this.wrappedIterator = it;
          this.filter = filter;
      }

      @Override
      public boolean hasNext() {
          while (wrappedIterator.hasNext()) {
              if (filter.test(wrappedIterator.next())) return true;
          }
          return false;
      }
  }
  ```

---

### **3. Alternatives**
| **Pattern**               | **Use When...**                                                                                     | **Trade-offs**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Iterator**              | Need uniform traversal for heterogeneous collections.                                              | No direct access to internal state; may require wrapper iterators for custom logic. |
| **Visitor Pattern**       | Need to perform operations on collection elements without changing their class.                     | More complex for large collections; violates Open/Closed Principle if collections change. |
| **Composite Pattern**     | Collections have nested structures (e.g., trees).                                                  | Overhead for flat collections; requires recursive traversal logic.             |

---

## **Query Examples**

### **Example 1: Traversing a List**
```java
// Client code
Aggregate<String> list = new ConcreteList();
list.add("Apple");
list.add("Banana");

Iterator<String> iterator = list.createIterator();
while (iterator.hasNext()) {
    System.out.println(iterator.next());  // Output: Apple, Banana
}
```

### **Example 2: Bidirectional Iteration**
```java
// Extend Iterator for backward traversal
public class BidirectionalListIterator<T> implements BidirectionalIterator<T> {
    private List<T> list;
    private int currentIndex;

    @Override
    public boolean hasNext() { return currentIndex < list.size(); }
    @Override
    public T next() { return list.get(currentIndex++); }
    @Override
    public boolean hasPrevious() { return currentIndex > 0; }
    @Override
    public T previous() { return list.get(--currentIndex); }
}

// Usage:
BidirectionalIterator<String> biIt = new BidirectionalListIterator<>(list);
while (biIt.hasPrevious()) {
    System.out.println(biIt.previous());  // Output: Banana, Apple
}
```

### **Example 3: Filtered Iteration**
```java
// Filter even numbers from a list
Aggregate<Integer> numbers = new ConcreteList<>();
numbers.add(1);
numbers.add(2);
numbers.add(3);

Iterator<Integer> filteredIt = new FilterIterator<>(
    numbers.createIterator(),
    num -> num % 2 == 0
);

while (filteredIt.hasNext()) {
    System.out.println(filteredIt.next());  // Output: 2
}
```

---

## **Best Practices**
1. **Encapsulate Iteration Logic**:
   - Avoid exposing internal collection structures (e.g., arrays, linked lists) directly.
   - Prefer `Iterator` over raw loops (e.g., `for (T item : collection)` is syntactic sugar for `Iterator`).

2. **Support Fail-Fast Iteration**:
   - Implement `ConcreteIterator` to throw `ConcurrentModificationException` if the collection is modified during iteration (common in Java’s `Iterator`).

3. **Lazy Evaluation**:
   - Defer computations until `next()` is called (e.g., for expensive operations like file parsing).

4. **Thread Safety**:
   - If collections are shared across threads, synchronize iterator creation or use thread-local iterators.

5. **Performance Considerations**:
   - Prefer lightweight iterators (e.g., array-based) over heavyweight ones (e.g., tree traversals) for large datasets.
   - Avoid `Iterator.remove()` in performance-critical loops if possible (it may require rehashing).

6. **Iteration Policies**:
   - Document whether iterators support `remove()`, `hasPrevious()`, or concurrent modifications.

---

## **Anti-Patterns**
| **Anti-Pattern**                          | **Problem**                                                                                     | **Solution**                                                                 |
|--------------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Exposing Internal State**               | Clients modify collection via iterator (e.g., `Iterator.remove()`).                             | Use `ConcreteAggregate`'s built-in removal methods instead.                   |
| **Tight Coupling to Collection Type**     | Iterator depends on specific collection implementation (e.g., array indices).                   | Abstract iteration logic in `ConcreteIterator`.                              |
| **Unbounded Iteration**                   | Infinite loops due to `hasNext()` logic errors.                                                 | Validate iterator state (e.g., `currentIndex` bounds).                        |
| **Ignoring Fail-Fast Requirements**       | Collection modifications during iteration cause undefined behavior.                             | Implement fail-fast checks or use thread-safe collections.                   |

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                                     | **When to Combine**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Composite**             | Collections can be nested (e.g., trees).                                                          | Use `Iterator` to traverse composite structures recursively.                         |
| **Visitor**               | Perform operations on collection elements without exposing their structure.                         | Combine with `Iterator` to traverse elements before applying visitor operations.    |
| **Chain of Responsibility** | Handle iteration events (e.g., logging, validation) during traversal.                              | Attach handlers to `Iterator` methods (e.g., `next()`).                             |
| **Template Method**       | Define iteration template (e.g., "for each element, do X then Y").                                  | Use `Template Method` to structure composite iteration logic.                      |

---

## **Example Code (Python)**
```python
from abc import ABC, abstractmethod

class Iterator(ABC):
    @abstractmethod
    def has_next(self):
        pass

    @abstractmethod
    def next(self):
        pass

class ListIterator(Iterator):
    def __init__(self, collection):
        self.collection = collection
        self.index = 0

    def has_next(self):
        return self.index < len(self.collection)

    def next(self):
        if not self.has_next():
            raise StopIteration
        return self.collection[self.index]

class ListAggregate:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def create_iterator(self):
        return ListIterator(self.items)

# Usage:
list_agg = ListAggregate()
list_agg.add("A")
list_agg.add("B")

iterator = list_agg.create_iterator()
while iterator.has_next():
    print(iterator.next())  # Output: A, B
```

---
**Key Takeaway**: The **Iterator Pattern** promotes clean, decoupled traversal by abstracting iteration logic. Use it to streamline code across diverse collections while maintaining flexibility and encapsulation.