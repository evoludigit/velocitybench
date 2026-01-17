# **[Pattern] TypeScript Language Patterns Reference Guide**

---

## **Overview**
TypeScript’s language patterns enable developers to write maintainable, type-safe, and scalable code. This guide covers core TypeScript features, advanced patterns, and best practices, including **typing systems, generics, utilities, decorators, and runtime checks**. Whether refining interfaces, optimizing performance, or enforcing consistency, these patterns help leverage TypeScript’s full potential while avoiding common antipatterns.

---

## **Schema Reference**

| **Pattern**             | **Purpose**                                                                 | **Key Features**                                                                 | **Example Use Case**                          |
|-------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|-----------------------------------------------|
| **1. Strong Typing**    | Enforce type safety to catch errors at compile time.                        | `type`, `interface`, `enum`, union/intersection types.                           | API contracts, form validation.              |
| **2. Generics**         | Reusable components with type flexibility.                               | `<T>`, constrained generics, mapped types (`Partial<T>`, `Pick<T>`).             | Generic utilities (e.g., `reduce` for arrays). |
| **3. Utility Types**    | Transform existing types without duplicating code.                         | `Partial<T>`, `Required<T>`, `Record<K, V>`, `Omit<T, K>`.                       | Dynamic form props, shallow copies.           |
| **4. Type Guards**      | Narrow types at runtime using type predicates.                             | `typeof`, `instanceof`, custom guards (`is X`).                                  | Type-safe routing, event handling.           |
| **5. Decorators**       | Modify behavior via metadata (e.g., logging, DI).                          | `@Component`, `@Injectable`, `@ts-ignore`.                                        | Dependency injection, logging middleware.    |
| **6. Mapped Types**     | Apply transformations to all properties of a type.                         | `Partial<{ a: string }> = { a?: string }`.                                       | Optional props, deep clones.                  |
| **7. Discriminated Unions** | Represent mutually exclusive states with a shared key.                  | `{ kind: "A"; value: string } \| { kind: "B"; value: number }`.                 | State machines, API responses.                |
| **8. Type Inference**   | Automatically derive types from literals/values.                          | `const x = 5` → `type x = 5`.                                                   | Reduce boilerplate in constants.              |
| **9. Conditional Types** | Resolve types based on conditions.                                          | `T extends U ? X : Y`.                                                           | Runtime-like logic in compile-time.          |
| **10. Advanced `in`**   | Mapped types with dynamic keys.                                             | `type Props = { [P in K]: V }`.                                                   | Dynamic component props.                     |
| **11. Runtime Checks**  | Bridge compile-time types with runtime assertions.                         | `assert`, `isTypeOf`, `zod`/`io-ts`.                                             | Validation, data serialization.              |
| **12. `unknown` vs `any`** | Safer alternative to `any` for untrusted data.                            | `unknown` requires type assertion vs. `any`’s dynamic bypass.                     | Third-party libraries, user input.           |
| **13. `extends` vs `&`** | Combine/intersect types (`&`) vs. inheritance (`extends`).                 | `interface Base { ... }` vs. `type Remixed = Base & New`.                         | Mixins, partial updates.                     |

---

## **Implementation Details**

### **1. Strong Typing**
- **`type` vs. `interface`**:
  - Use `interface` for object shapes; `type` for unions, tuples, or computed types.
  - Example:
    ```ts
    interface User { name: string; age: number; }
    type Status = "active" | "inactive";
    ```
- **Exact Object Types** (`as const`):
  Prevents property reordering in objects.
  ```ts
  const exact = { a: 1, b: 2 } as const; // { readonly a: 1; readonly b: 2 }
  ```

### **2. Generics**
- **Basic Usage**:
  ```ts
  function identity<T>(arg: T): T { return arg; }
  ```
- **Constrained Generics**:
  ```ts
  function length<T extends { length: number }>(arr: T): number {
    return arr.length;
  }
  ```

### **3. Utility Types**
- **Transform Properties**:
  ```ts
  type ReadonlyUser<T> = { readonly [P in keyof T]: T[P] };
  ```
- **Dynamic Keys**:
  ```ts
  type NumericKeys<T> = { [K in keyof T]: T[K] extends number ? K : never }[keyof T];
  ```

### **4. Type Guards**
- **Custom Guards**:
  ```ts
  function isString(val: unknown): val is string {
    return typeof val === "string";
  }
  ```
- **`in` Operator**:
  ```ts
  if ("length" in obj && typeof obj.length === "number") { ... }
  ```

### **5. Decorators**
- **Metadata Reflection**:
  ```ts
  @Reflect.metadata("design:type", Number)
  property count: number;
  ```
- **Runtime Usage**:
  ```ts
  console.log(Reflect.getMetadata("design:type", obj, "count")); // Number
  ```

### **6. Discriminated Unions**
- **Pattern Matching**:
  ```ts
  type Event = { type: "click"; x: number } | { type: "scroll"; distance: number };
  function handleEvent(e: Event) {
    switch (e.type) {
      case "click": return e.x;
      case "scroll": return e.distance;
    }
  }
  ```

### **7. Conditional Types**
- **Derived Constraints**:
  ```ts
  type Flatten<T> = T extends any[] ? T[number] : T; // Flatten arrays.
  ```

### **8. `unknown` Best Practices**
- **Safe Unwrapping**:
  ```ts
  const data: unknown = fetchData();
  if (typeof data === "string") { /* Type-safe */ }
  ```

### **9. Runtime Checks**
- **`zod` Validation**:
  ```ts
  import { z } from "zod";
  const schema = z.object({ name: z.string().min(3) });
  const parsed = schema.parse(rawData); // Throws if invalid.
  ```

---

## **Query Examples**

### **1. Type-Safe API Client**
```ts
interface ApiResponse<T> {
  data: T;
  error: null | { message: string };
}

async function fetchUser(id: string): Promise<ApiResponse<User>> {
  const res = await fetch(`/api/users/${id}`).then(res => res.json());
  return res; // TypeScript infers `ApiResponse<User>`.
}
```

### **2. Generic Utility: `DeepReadonly`**
```ts
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};
const obj: DeepReadonly<{ a: { b: number } }> = { a: { b: 42 } }; // b is readonly.
```

### **3. Type Guard for Optional Fields**
```ts
function hasField<T extends object>(obj: T, field: keyof T): obj is T & { [K in keyof T]: T[K] } {
  return field in obj;
}
if (hasField(user, "age")) { user.age.toFixed(); }
```

### **4. Decorator for Logging**
```ts
function logMethod(target: any, key: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function(...args: any[]) {
    console.log(`Calling ${key} with`, args);
    return original.apply(this, args);
  };
}

class Calculator {
  @logMethod
  add(a: number, b: number) { return a + b; }
}
```

---

## **Related Patterns**

| **Pattern**               | **Connection to TypeScript**                                                                 | **Reference**                     |
|---------------------------|--------------------------------------------------------------------------------------------|-----------------------------------|
| **Dependency Injection**  | Use decorators (`@Injectable`) or `Reflect.metadata` for DI containers.                   | [Angular DI](https://angular.io/guide/dependency-injection) |
| **State Management**      | Type-safe Redux/Zustand stores with discriminated unions for actions.                      | [Zustand Docs](https://zustand-demo.pmnd.rs/) |
| **Testing Utilities**     | Mock types with `jest.mock` + `Partial<T>`.                                                 | [TypeScript Jest Guide](https://typed-jest.com/) |
| **Microservices**         | Contract-first APIs with `openapi-types` + TypeScript schemas.                           | [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator) |
| **Build Systems**         | `tsup`/`esbuild` for optimized bundling with type checking.                               | [tsup](https://tsup.egoist.dev/)   |

---

## **Common Pitfalls & Mitigations**

| **Issue**                          | **Symptom**                          | **Solution**                                                                 |
|-------------------------------------|--------------------------------------|------------------------------------------------------------------------------|
| Overusing `any`                     | Loss of type safety.                  | Replace with `unknown` or stricter unions.                                   |
| Complex nested generics            | Hard-to-read type errors.            | Break into smaller mapped types or use `Readonly<T>`.                        |
| Discriminated union leaks          | `type` instead of `interface`.       | Use `type` with a shared discriminator (e.g., `kind`).                       |
| Runtime type assertion bugs        | Type checks bypassed.               | Prefer `isTypeOf` guards or libraries like `io-ts`.                          |
| Decorator reflection warnings      | `@ts-ignore` required.               | Enable `experimentalDecorators` in `tsconfig.json`.                           |

---
**Notes**:
- **Performance**: Excessive type complexity can slow down compilation. Profile with `--showCircularDependencies`.
- **Tooling**: Combine with `eslint-plugin-import` + `typescript-eslint` for linter rules.