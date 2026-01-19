# **Debugging Polymorphic Union Types: A Troubleshooting Guide**

## **Introduction**
Polymorphic union types (e.g., JavaScript/TypeScript's `type Union<T extends Type> = T | AnotherType`, or similar constructs in other languages) allow us to work with multiple related types interchangeably. While powerful, they introduce complexity that can lead to runtime and compile-time errors.

This guide covers common issues, debugging techniques, and prevention strategies for polymorphic union types.

---

## **Symptom Checklist**
Before diving deep, check if your issue matches any of these symptoms:

✅ **"Cannot assign type 'X' to type 'Y'"** (TypeScript) or similar type assertion errors.
✅ **Runtime errors** like `Cannot read property 'z' of undefined` when working with union types.
✅ **Inconsistent discriminants** (e.g., `Discriminant` property mismatches in nested objects).
✅ **Unexpected behavior** when type guards (e.g., `is` checks in TypeScript) fail.
✅ **Compile-time errors** when extending or modifying union types.

If any of these apply, proceed to the next sections.

---

## **Common Issues & Fixes (with Code Examples)**

### **1. Missing or Incorrect Type Guards**
**Problem:**
A type guard (e.g., `if (obj.type === "User") { ... }`) fails to narrow the type correctly, leading to runtime errors.

**Example:**
```typescript
type User = { name: string; role: "user" };
type Admin = { name: string; role: "admin" };
type Person = User | Admin;

function processPerson(person: Person) {
  if (person.role === "user") {  // Type guard fails if `role` is missing
    console.log(person.name.toUpperCase()); // May still be called on `Admin` if `role` is missing
  }
}
```

**Fix:**
Ensure all types in the union have the discriminant (`role` in this case) and handle edge cases.

```typescript
type SafePerson = User & { role: string } | Admin; // Explicitly mark required fields

function processPerson(person: SafePerson) {
  if (!person.role) throw new Error("Invalid role"); // Guard fails safely
  if (person.role === "user") {
    console.log(person.name.toUpperCase());
  }
}
```

---

### **2. Mismatched Nested Type Structures**
**Problem:**
Different types in the union have different structures, causing type errors.

**Example:**
```typescript
type Circle = { kind: "circle"; radius: number };
type Square = { kind: "square"; side: number }; // Missing `radius`

type Shape = Circle | Square;

function area(shape: Shape) {
  if (shape.kind === "circle") {
    return Math.PI * shape.radius ** 2; // Error: `radius` may not exist
  }
}
```

**Fix:**
Use **intersection types** or **strict type checks** to enforce consistency.

```typescript
type Shape = Circle & { kind: "circle" | "square" } | Square;

function area(shape: Shape) {
  if (shape.kind === "circle") {
    return Math.PI * (shape as Circle).radius ** 2; // Explicit cast (if safe)
  }
}
```

---

### **3. Discriminant Property Mismatch**
**Problem:**
A discriminator (e.g., `kind`) is missing or inconsistent across types.

**Example:**
```typescript
type Circle = { kind: "circle"; radius: number };
type Polygon = { kind: "polygon"; sides: number }; // Missing `kind`

type Shape = Circle | Polygon; // TypeScript warns about missing `kind`
```

**Fix:**
Ensure all types in the union define the discriminant.

```typescript
type Shape = Circle & { kind: string } | Polygon; // Explicitly require `kind`
```

---

### **4. Overly Broad Type Guards**
**Problem:**
A guard like `if (obj instanceof MyClass)` fails because the type is too generic.

**Example (JavaScript):**
```javascript
class User { constructor(name) { this.name = name; } }
class Admin extends User { constructor(name) { super(name); this.perms = []; } }

function process(obj) {
  if (obj instanceof User) { // Admin also instanceof User
    console.log(obj.name); // Works for both but may expose `perms` accidentally
  }
}
```

**Fix:**
Use **type-specific checks** or design discriminants differently.

```javascript
function process(obj) {
  if (obj instanceof Admin) { // More precise
    console.log(obj.perms);
  } else if (obj instanceof User) { // Fallback
    console.log(obj.name);
  }
}
```

---

### **5. Runtime vs. Compile-Time Mismatches**
**Problem:**
A type is valid at compile time but fails at runtime due to strict checks.

**Example:**
```typescript
type User = { name: string; age?: number };
type Robot = { model: string; battery?: number };

function greet(obj: User | Robot) {
  if ("name" in obj) { // Narrows to `User`, but `age` may be missing
    console.log(obj.name);
  }
}
```

**Fix:**
Handle optional properties explicitly.

```typescript
if ("age" in obj) {
  console.log(`User: ${obj.name}, Age: ${obj.age}`);
} else {
  console.log(`Robot: ${("model" in obj ? obj.model : "Unknown")}`);
}
```

---

## **Debugging Tools & Techniques**

### **1. TypeScript’s `keyof` and `in` Operator**
Use `in` to check for type safety before access:

```typescript
if ("property" in obj) {
  console.log(obj.property); // Safe
}
```

### **2. `typeof` and `instanceof` Checks**
Use `typeof` for primitives and `instanceof` for classes:

```javascript
if (typeof x === "number") {
  // Safe to use x as a number
}
```

### **3. `asserts` and Explicit Type Assertions**
Sometimes, you need to assert types when type narrowing fails:

```typescript
const obj = getObject(); // Returns `User | Admin`
const user = obj as User; // Assert if you're sure
```

### **4. Debugging with `console.log` + Type Predicates**
Log properties to confirm type structure:

```typescript
console.log("Type:", typeof obj.kind); // Helps verify runtime behavior
```

### **5. TypeScript’s `type` and `interface` Deep Comparison**
Use `typeof` to inspect types interactively:

```typescript
console.log(typeof { x: 1 }); // "object"
```

---

## **Prevention Strategies**

### **1. Enforce Discriminated Unions Strictly**
Always design unions with a clear discriminant (e.g., `kind`, `type`).

```typescript
type User = { type: "user"; name: string };
type Admin = { type: "admin"; permissions: string[] };
type Person = User | Admin; // Safe narrowing
```

### **2. Use Type Guards Everywhere**
Avoid magic properties—always use explicit guards.

```typescript
if (typeof obj.type === "string" && obj.type === "user") {
  // Safe
}
```

### **3. Avoid Overly Generic Types**
Prefer specific types over broad unions when possible.

```typescript
// Bad: Too broad
type Entity = User | Admin | Robot;

// Better: Break into separate cases
type UserEntity = User;
type AdminEntity = Admin;
```

### **4. Leverage `readonly` and `required` Properties**
Mark critical fields as required to catch errors early.

```typescript
interface User {
  name: string;      // Required
  age?: number;      // Optional
}
```

### **5. Write Unit Tests for Edge Cases**
Test with `null`, `undefined`, and unexpected inputs.

```typescript
test("handles missing discriminator", () => {
  expect(() => process({ name: "Bob" } as any)).toThrow();
});
```

---

## **Final Checklist for Resolution**
✔ **Check discriminator presence** in all union types.
✔ **Verify type guards** are exhaustive.
✔ **Test edge cases** (missing props, unexpected shapes).
✔ **Use `console.log` + `instanceof`/`typeof`** for runtime debugging.
✔ **Refactor overly broad unions** into specific types.

---

## **Conclusion**
Polymorphic union types are powerful but require careful handling. By following this guide, you can systematically debug issues by focusing on **type narrowing, discriminators, and runtime safety checks**. Always prefer compile-time safety over runtime assumptions.

**Next Steps:**
- Review your current union types.
- Apply strict type guards.
- Test edge cases thoroughly.