```markdown
---
title: "Input Type Definition: The Missing Piece in Your Backend Stack"
date: 2023-11-15
tags: ["backend engineering", "api design", "database patterns", "input validation", "ddd"]
draft: false
---

# **Input Type Definition: The Missing Piece in Your Backend Stack**

As backend engineers, we’re constantly balancing between flexibility and structure. We want APIs that are intuitive to consume, databases that are performant, and business logic that’s maintainable. But here’s a problem: **most systems treat input as an afterthought**—a loose collection of JSON fields that changes with every request.

Enter the **Input Type Definition** pattern—a systematic way to document, validate, and reuse input contracts across your application. This isn’t just about validation; it’s about **shaping how clients interact with your system**, enforcing invariants early, and making your codebase more predictable.

By the end of this post, you’ll understand:
✅ Why loose input handling leads to technical debt
✅ How Input Type Definitions (ITDs) work in practice
✅ Real-world implementations in Go, TypeScript, and Java
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Input Without a Blueprint**

Imagine a REST API for a booking system. A typical `/bookings` endpoint might accept:

```json
{
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "price": 499.99,
  "guests": 4,
  "payment_method": "credit_card"
}
```

At first glance, this seems fine. But what happens when:
- The client sends `"price": "499"` (string instead of number)?
- The `end_date` is earlier than `start_date`?
- A new field like `"taxes": 50` is introduced because the frontend team “forgot” to sync with the API spec?

Without explicit input contracts, your application becomes:
- **Fragile**: Unexpected inputs crash your app or lead to inconsistent behavior.
- **Slow to evolve**: Every field change requires documentation updates and client-side fixes.
- **Hard to debug**: Errors surface only after validation, making tracing difficult.

Worse, **this problem scales**. If you’re using GraphQL, it becomes even trickier—schema drift between frontend and backend is inevitable without strict validation.

---

## **The Solution: Input Type Definitions (ITDs)**

Input Type Definitions (ITDs) are **explicit contracts** that enforce:
1. **Field names and types** (e.g., `"price"` must be a number).
2. **Validation rules** (e.g., `"guests"` must be ≥1).
3. **Optional/required fields** (e.g., `"taxes"` may be omitted).
4. **Nested structures** (e.g., `"user": { "id": string, "name": string }`).

An ITD isn’t just a validation layer—it’s a **shared language** between:
- API consumers (frontend, mobile apps, third-party integrations).
- Backend services (handling requests, transformations, and business logic).
- Documentation (auto-generated Swagger/OpenAPI specs).

### **Key Benefits of ITDs**
- **Early error detection**: Fail fast with meaningful messages.
- **Self-documenting APIs**: Fields define their purpose (e.g., `"price"` has a `max_value` constraint).
- **Testability**: Validate inputs in unit tests before they hit your database.
- **Evolution safety**: New fields can be added without breaking clients (with backward-compatibility strategies).

---

## **Components of an Input Type Definition**

An ITD typically includes:
1. **Field Definitions** – Names, types, and constraints.
2. **Validation Logic** – Custom rules (e.g., `"tax_rate" must match "price"`).
3. **Transformations** – Normalizing inputs (e.g., `ISO 8601` dates → `time.Time`).
4. **Dependency Injection** – Reusing ITDs across endpoints (e.g., a `UserLogin` ITD for both `/login` and `/verify`).

### **Example ITD (Conceptual)**
```json
{
  "type": "Booking",
  "fields": [
    {
      "name": "start_date",
      "type": "string",
      "format": "date",
      "constraints": { "min": "2024-01-01" },
      "description": "ISO 8601 date (inclusive)"
    },
    {
      "name": "end_date",
      "type": "string",
      "format": "date",
      "constraints": {
        "gt": "start_date", // end_date > start_date
        "max": "2024-12-31"
      }
    },
    {
      "name": "payment_method",
      "type": "enum",
      "values": ["credit_card", "paypal", "bank_transfer"]
    }
  ]
}
```

---

## **Code Examples: Implementing ITDs**

Let’s explore ITD implementations in three languages: **Go, TypeScript, and Java**.

---

### **1. Go: Structs + ` validator ` Package**
Go’s statically typed nature makes ITDs straightforward.

#### **Step 1: Define Input Structs**
```go
package booking

import (
	"time"

	"github.com/go-playground/validator/v10"
)

type BookingInput struct {
	StartDate     string   `json:"start_date" validate:"required,date_format=2006-01-02"`
	EndDate       string   `json:"end_date" validate:"required,gtfield=StartDate,date_format=2006-01-02"`
	Price         float64  `json:"price" validate:"required,gt=0"`
	Guests        int      `json:"guests" validate:"required,min=1,max=10"`
	PaymentMethod string   `json:"payment_method" validate:"required,oneof=credit_card paypal bank_transfer"`
	Taxes         *float64 `json:"taxes,omitempty" validate:"omitempty,min=0"`
}

var validate = validator.New()
```

#### **Step 2: Validate in a Handler**
```go
func CreateBooking(w http.ResponseWriter, r *http.Request) {
	var input BookingInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := validate.Struct(input); err != nil {
		http.Error(w, validate.ErrorsByField(input), http.StatusBadRequest)
		return
	}

	// Proceed with business logic...
}
```

**Pros**:
- Simple, leverages Go’s struct tags.
- Works well with JSON unmarshalling.

**Cons**:
- Validation messages aren’t as customizable.
- No built-in support for nested structures.

---

### **2. TypeScript: Zod or Joi**
TypeScript’s type system + runtime validation libraries make ITDs expressive.

#### **Example with Zod**
```typescript
import { z } from "zod";

const bookingSchema = z.object({
  start_date: z.string().datetime({
    required_error: "Start date is required",
    invalid_type_error: "Must be a date string",
  }),
  end_date: z.string().datetime({
    required_error: "End date is required",
  }).refine((date, ctx) => {
    const startDate = new Date(booking.start_date);
    if (date < startDate) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "End date must be after start date",
      });
    }
    return date >= startDate;
  }),
  price: z.number().min(1, "Price must be ≥ $1"),
  guests: z.number().int().min(1, "At least 1 guest required"),
  payment_method: z.enum(["credit_card", "paypal", "bank_transfer"]),
});

// Usage in an Express route
app.post("/bookings", (req, res) => {
  const result = bookingSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.flatten() });
  }

  const validatedInput = result.data;
  // Proceed with logic...
});
```

**Pros**:
- Compile-time type safety + runtime validation.
- Highly customizable error messages.
- Supports nested schemas (e.g., `UserInput extends z.object({...})`).

**Cons**:
- Overkill for simple APIs.
- Zod/Joi add runtime overhead.

---

### **3. Java: Lombok + Jackson + Bean Validation**
Java’s ecosystem offers robust ITD support.

#### **Step 1: Define a DTO with Annotations**
```java
import jakarta.validation.constraints.*;
import lombok.Data;

@Data
public class BookingInput {
    @NotBlank
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}")
    private String startDate;

    @NotBlank
    @Pattern(regexp = "\\d{4}-\\d{2}-\\d{2}")
    @FutureOrPresent
    private String endDate;

    @DecimalMin("0.01")
    private BigDecimal price;

    @Min(1)
    @Max(10)
    private int guests;

    @NotBlank
    @Pattern(regexp = "credit_card|paypal|bank_transfer")
    private String paymentMethod;
}
```

#### **Step 2: Validate with Spring Boot**
```java
@RestController
@RequestMapping("/bookings")
public class BookingController {

    @PostMapping
    public ResponseEntity<String> createBooking(@Valid @RequestBody BookingInput input) {
        // Validation happens automatically
        // Proceed with logic...
        return ResponseEntity.ok("Booking created");
    }
}
```

**Pros**:
- Standardized with Jakarta Bean Validation.
- Works seamlessly with Spring.
- Supports custom validators.

**Cons**:
- Verbose annotations.
- Less flexible for complex rules.

---

## **Implementation Guide: Best Practices**

### **1. Centralize ITDs**
Store ITDs in a shared module (e.g., `pkg/inputs`) to avoid duplication.

```go
// pkg/inputs/booking.go
package inputs

import "github.com/go-playground/validator/v10"

type BookingInput struct {
    // ... fields ...
}

func Validate(input *BookingInput) error {
    return validate.Struct(input)
}
```

### **2. Use Enums for Closed Fields**
```typescript
const PaymentMethod = z.enum(["credit_card", "paypal", "bank_transfer"]);
```

**Why?** Prevents typos and ensures all values are known at design time.

### **3. Support Backward Compatibility**
For breaking changes (e.g., renaming `end_date` to `end_datetime`):
- Add a deprecation header in API responses.
- Use feature flags to roll out changes gradually.

### **4. Generate Documentation**
Automate Swagger/OpenAPI specs from ITDs:
- **Go**: Use `swaggo/swag`.
- **TypeScript**: `zod-to-openapi`.
- **Java**: SpringDoc OpenAPI.

---

## **Common Mistakes to Avoid**

### **1. Over-engineering Validation**
❌ Don’t validate everything at the JSON level—some rules belong in business logic.
✅ Example:
```go
// Bad: Validate price ≥ 0 in the struct tag.
type OrderInput struct {
    Price float64 `validate:"gt=0"` // Should this be in the DB layer?
}

// Good: Keep price ≥ 0 in the DB schema (e.g., `NOT NULL, CHECK (price > 0)`).
```

### **2. Ignoring Performance**
🚀 **Runtime validation adds overhead**. For high-throughput APIs:
- Cache parsed inputs (e.g., Redis for repeated queries).
- Use lightweight libraries (e.g., `go-playground/validator` vs. Mappers).

### **3. Not Handling Partial Updates**
🔄 APIs often support PATCH requests with partial updates. Ensure your ITDs handle this:
```typescript
const updateBookingSchema = z.object({
  start_date: z.string().datetime().optional(),
  price: z.number().optional(),
  // ... other optional fields ...
});
```

### **4. Silent Failures**
❌ Allowing undefined fields to silently drop data.
✅ **Be explicit**: Log warnings or return `400 Bad Request`.

---

## **Key Takeaways**

| ** Lesson **               | ** Action Item **                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| Inputs define your API’s contract. | Treat ITDs like database schemas—design them first.                          |
| Validation should fail fast. | Catch errors at the request boundary, not in business logic.                  |
| Reuse ITDs across endpoints. | Avoid duplication (e.g., `UserLogin` for `/login` and `/refresh-token`).      |
| Document constraints.      | Add `description` fields to ITDs for auto-generated docs.                      |
| Plan for evolution.        | Use backward-compatible changes (e.g., `v2/endpoints`).                      |
| Balance strictness and flexibility. | Let consumers know what’s optional vs. required.                          |

---

## **Conclusion**

Input Type Definitions are the **glue** between your API consumers and backend logic. They:
✔ Make APIs more predictable.
✔ Reduce debuggability by catching errors early.
✔ Enable better documentation and self-service.

**Start small**: Apply ITDs to your most critical endpoints first (e.g., `/users`, `/orders`). As your system grows, you’ll see how much headache they prevent.

### **Further Reading**
- [Go Playground Validator Docs](https://github.com/go-playground/validator)
- [Zod Documentation](https://github.com/colinhacks/zod)
- [Jakarta Bean Validation](https://jakarta.ee/specifications/bean-validation/)

**Your turn**: How do you handle input validation in your projects? Share your thoughts—or better yet, open a PR to improve this pattern! 🚀
```

---
**Word Count**: ~1,850
**Tone**: Practical, code-first, and balanced (tradeoffs discussed).
**Audience**: Advanced backend engineers (Go/TypeScript/Java examples).
**Structure**: Clear sections with actionable examples.